import shutil
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Any, Iterable

import os

from tqdm import tqdm

from sinner.State import State
from sinner.Status import Status, Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.utilities import list_class_descendants, resolve_relative_path, is_image, is_video, get_mem_usage, suggest_max_memory, get_app_dir, TEMP_DIRECTORY
from sinner.validators.AttributeLoader import Rules


class BatchProcessingCore(Status):
    target_path: str
    output_path: str
    frame_processor: List[str]
    temp_dir: str
    extract_frames: bool
    keep_frames: bool
    max_memory: int

    parameters: Namespace

    _statistics: dict[str, int] = {'mem_rss_max': 0, 'mem_vms_max': 0, 'limits_reaches': 0}

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': 'max-memory',  # key defined in Sin, but class can be called separately in tests
                'default': suggest_max_memory(),
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'valid': lambda: os.path.exists(self.target_path),
                'help': 'Path to the target file or directory (depends on used frame processors set)'
            },
            {
                'parameter': {'output', 'output-path'},
                'attribute': 'output_path',
                'default': lambda: self.suggest_output_path(),
                'help': 'Path to the resulting file or directory (depends on used frame processors set and target)'
            },
            {
                'parameter': {'frame-processor', 'processor', 'processors'},
                'attribute': 'frame_processor',
                'default': ['FaceSwapper'],
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor'),
                'help': 'The set of frame processors to handle the target'
            },
            {
                'parameter': 'keep-frames',
                'default': False,
                'help': 'Keep temporary frames after processing'
            },
            {
                'parameter': 'temp-dir',
                'default': lambda: self.suggest_temp_dir(),
                'help': 'Select the directory for temporary files'
            },
            {
                'module_help': 'The batch processing handler'
            }
        ]

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        self.preview_processors = {}
        super().__init__(parameters)

    def run(self) -> None:
        current_target_path = self.target_path
        temp_resources: List[str] = []  # list of temporary created resources
        for processor_name in self.frame_processor:
            current_processor = BaseFrameProcessor.create(processor_name, self.parameters)
            handler = self.suggest_handler(current_target_path, self.parameters)
            state = State(parameters=self.parameters, target_path=current_target_path, temp_dir=self.temp_dir, frames_count=handler.fc, processor_name=processor_name)

            if state.is_finished:
                self.update_status(f'Processing with {processor_name} already done ({state.processed_frames_count}/{state.frames_count})')
            else:
                if state.is_started:
                    self.update_status(f'Temp resources for this target already exists with {state.processed_frames_count} frames processed, continue processing with {state.processor_name}')

                self.process(current_processor, handler, state)
                current_processor.release_resources()
            current_target_path = state.path
            temp_resources.append(state.path)

        if current_target_path is not None:
            handler = self.suggest_handler(self.target_path, self.parameters)
            handler.result(from_dir=current_target_path, filename=self.output_path, audio_target=self.target_path)
        else:
            self.update_status('Target path is empty, ignoring', mood=Mood.BAD)

        if self.keep_frames is False:
            self.update_status('Deleting temp resources')
            for dir_path in temp_resources:
                shutil.rmtree(dir_path, ignore_errors=True)

    @staticmethod
    def process_frames(frame_num: int, processor: BaseFrameProcessor, handler: BaseFrameHandler, state: State) -> None:  # type: ignore[type-arg]
        try:
            frame_num, frame, frame_name = handler.extract_frame(frame_num)
            state.save_temp_frame(processor.process_frame(frame), frame_name or frame_num)
        except Exception as exception:
            processor.update_status(message=str(exception), mood=Mood.BAD)
            quit()

    def process(self, processor: BaseFrameProcessor, handler: BaseFrameHandler, state: State) -> None:
        handler.current_frame_index = state.processed_frames_count
        with tqdm(
                total=state.frames_count,
                desc=state.processor_name, unit='frame',
                dynamic_ncols=True,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
                initial=state.processed_frames_count,
        ) as progress:
            self.multi_process_frame(frames_iterator=handler, state=state, processor=processor, progress=progress)
        _, lost_frames = state.final_check()
        if lost_frames:
            with tqdm(
                    total=len(lost_frames),
                    desc="Processing lost frames", unit='frame',
                    dynamic_ncols=True,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
            ) as progress:
                self.multi_process_frame(frames_iterator=lost_frames, state=state, processor=processor, progress=progress)
        is_ok, _ = state.final_check()
        if not is_ok:
            raise Exception("Something went wrong on processed frames check")

    def multi_process_frame(self, processor: BaseFrameProcessor, frames_iterator: BaseFrameHandler | Iterable[int], state: State, progress: tqdm) -> None:  # type: ignore[type-arg]
        def process_done(future_: Future[None]) -> None:
            futures.remove(future_)
            progress.set_postfix(self.get_postfix(len(futures)))
            progress.update()

        with ThreadPoolExecutor(max_workers=processor.execution_threads) as executor:
            futures: list[Future[None]] = []
            for frame in frames_iterator:
                future: Future[None] = executor.submit(self.process_frames, frame, processor, frames_iterator, state)
                future.add_done_callback(process_done)
                futures.append(future)
                progress.set_postfix(self.get_postfix(len(futures)))
                if get_mem_usage('vms', 'g') >= self.max_memory:
                    futures[:1][0].result()
                    self._statistics['limits_reaches'] += 1
            for completed_future in as_completed(futures):
                completed_future.result()

    def get_mem_usage(self) -> str:
        mem_rss = get_mem_usage()
        mem_vms = get_mem_usage('vms')
        if self._statistics['mem_rss_max'] < mem_rss:
            self._statistics['mem_rss_max'] = mem_rss
        if self._statistics['mem_vms_max'] < mem_vms:
            self._statistics['mem_vms_max'] = mem_vms
        return '{:.2f}'.format(mem_rss).zfill(5) + 'MB [MAX:{:.2f}'.format(self._statistics['mem_rss_max']).zfill(5) + 'MB]' + '/' + '{:.2f}'.format(mem_vms).zfill(5) + 'MB [MAX:{:.2f}'.format(
            self._statistics['mem_vms_max']).zfill(5) + 'MB]'

    def get_postfix(self, futures_length: int) -> dict[str, Any]:
        postfix = {
            'memory_usage': self.get_mem_usage(),
            'futures': futures_length,
        }
        if self._statistics['limits_reaches'] > 0:
            postfix['limit_reaches'] = self._statistics['limits_reaches']
        return postfix

    def suggest_output_path(self) -> str:
        target_name, target_extension = os.path.splitext(os.path.basename(self.target_path))
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), 'result-' + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, 'result-' + target_name + target_extension)
        return self.output_path

    @staticmethod
    def suggest_handler(target_path: str | None, parameters: Namespace) -> BaseFrameHandler:  # todo: refactor this
        if target_path is None:
            raise Exception("The target path is not set")
        if os.path.isdir(target_path):
            return DirectoryHandler(target_path, parameters)
        if is_image(target_path):
            return ImageHandler(target_path, parameters)
        if is_video(target_path):
            return VideoHandler(target_path, parameters)
        raise NotImplementedError("The handler for current target type is not implemented")

    def suggest_temp_dir(self) -> str:
        return self.temp_dir if self.temp_dir is not None else os.path.join(get_app_dir(), TEMP_DIRECTORY)