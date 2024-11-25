import shutil
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Any, Iterable, Callable

import os

from pathvalidate import is_valid_filepath, ValidationError, validate_filepath
from tqdm import tqdm

from sinner.models.State import State
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.models.NumberedFrame import NumberedFrame
from sinner.models.status.StatusMixin import StatusMixin
from sinner.models.status.Mood import Mood
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import list_class_descendants, resolve_relative_path, is_image, is_video, get_mem_usage, suggest_max_memory, path_exists, is_dir, normalize_path, suggest_execution_threads, suggest_temp_dir
from sinner.validators.AttributeLoader import Rules, AttributeLoader


class BatchProcessingCore(AttributeLoader, StatusMixin):
    target_path: str
    output_path: str
    frame_processor: List[str]
    temp_dir: str
    extract_frames: bool
    keep_frames: bool
    max_memory: int
    execution_threads: int

    parameters: Namespace

    _statistics: dict[str, int] = {'mem_rss_max': 0, 'mem_vms_max': 0, 'limits_reaches': 0}
    _output_file: str | None = None  # despite the output_path value, the output file name can be changed during the execution process

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'max-memory',  # key defined in Sin, but class can be called separately in tests
                'default': suggest_max_memory(),
            },
            {
                'parameter': 'execution-threads',
                'type': int,
                'default': suggest_execution_threads(),
                'help': 'The count of simultaneous processing threads'
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'valid': lambda: path_exists(self.target_path),
                'filter': lambda: normalize_path(self.target_path),
                'required': True,
                'help': 'Path to the target file or directory (depends on used frame processors set)'
            },
            #  output_path can be:
            #   - a correct file path which will be used as is,
            #   - a correct path to a directory which will be used to save the result with an autogenerated file name
            #   - empty, to use target's directory as an output directory with an autogenerated file name
            {
                'parameter': {'output', 'output-path'},
                'attribute': 'output_path',
                'valid': lambda: self.output_path is None or is_valid_filepath(self.output_path, "auto"),
                'filter': lambda: None if self.output_path is None else normalize_path(self.output_path),
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
                'default': lambda: suggest_temp_dir(self.temp_dir),
                'help': 'Select the directory for temporary files'
            },
            {
                'module_help': 'The batch processing handler'
            }
        ]

    def configure_output_filename(self, prefix: str = 'result') -> None:
        if self.output_path is None:
            self._output_file = os.path.join(os.path.dirname(self.target_path), f'{prefix}-{os.path.basename(self.target_path)}')
        elif self._output_file == self.output_path:  # fixed path was passed, and it should stay fixed
            return
        else:
            try:
                validate_filepath(self.output_path, "auto")
                if is_dir(self.output_path):
                    self._output_file = os.path.join(self.output_path, f'{prefix}-{os.path.basename(self.target_path)}')
                else:
                    self._output_file = self.output_path
            except ValidationError as e:
                #  should never happen, output_path is validated in the rules
                raise Exception(f'Output filename {self.output_path} is invalid, reason: {e.reason}')

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        super().__init__(parameters)
        self.configure_output_filename()

    def run(self) -> None:
        current_target_path = self.target_path
        temp_resources: List[str] = []  # list of temporary created resources
        for processor_name in self.frame_processor:
            current_processor = BaseFrameProcessor.create(processor_name, self.parameters)
            handler = self.suggest_handler(current_target_path, self.parameters)
            state = State(parameters=self.parameters, target_path=current_target_path, temp_dir=self.temp_dir, frames_count=handler.fc, processor_name=processor_name)
            current_processor.configure_state(state)
            current_processor.configure_output_filename(self.configure_output_filename)
            if state.is_finished:
                self.update_status(f'Processing with {processor_name} already done ({state.processed_frames_count}/{state.frames_count})')
            else:
                if state.is_started:
                    self.update_status(f'Temp resources for this target already exists with {state.processed_frames_count} frames processed, continue processing with {state.processor_name}')
                if current_processor.self_processing:
                    current_processor.process(handler, state)
                else:
                    self.update_status(f'Processing with {processor_name} start')
                    self.process(current_processor, handler, state)
                current_processor.release_resources()
                self.update_status(f'{processor_name} release resources done')
            current_target_path = state.path
            temp_resources.append(state.path)

        if current_target_path is not None:
            handler = self.suggest_handler(self.target_path, self.parameters)
            self.update_status(f'{handler.__class__} suggested as handler, resulting')
            handler.result(from_dir=current_target_path, filename=str(self._output_file), audio_target=self.target_path)
            self.update_status(f'Video should be ready: {current_target_path}')
        else:
            self.update_status('Target path is empty, ignoring', mood=Mood.BAD)

        if self.keep_frames is False:
            self.update_status('Deleting temp resources')
            for dir_path in temp_resources:
                self.update_status(f'rmtree: {dir_path}')
                shutil.rmtree(dir_path, ignore_errors=True)
        else:
            self.update_status('Temp resources kept.')

    def process_frame(self, frame_num: int, extract: Callable[[int], NumberedFrame], process: Callable[[Frame], Frame], save: Callable[[NumberedFrame], None]) -> None:
        try:
            numbered_frame = extract(frame_num)
            numbered_frame.frame = process(numbered_frame.frame)
            save(numbered_frame)
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            quit()

    def process(self, processor: BaseFrameProcessor, handler: BaseFrameHandler, state: State) -> None:
        handler.current_frame_index = state.processed_frames_count
        self.update_status(f'Start multiprocessing')
        with tqdm(
                total=state.frames_count,
                desc=state.processor_name, unit='frame',
                dynamic_ncols=True,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
                initial=state.processed_frames_count,
        ) as progress:

            self.multi_process_frame(processor=processor, frames=handler, extract=handler.extract_frame, save=state.save_temp_frame, progress=progress)
        self.update_status(f'Processing done')
        _, lost_frames = state.final_check()
        self.update_status(f'Final check done: {lost_frames} lost')
        if lost_frames:
            with tqdm(
                    disable=True,
                    total=len(lost_frames),
                    desc="Processing lost frames", unit='frame',
                    dynamic_ncols=True,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
            ) as progress:
                self.multi_process_frame(processor=processor, frames=lost_frames, extract=handler.extract_frame, save=state.save_temp_frame, progress=progress)
        is_ok, _ = state.final_check()
        if not is_ok:
            raise Exception("Something went wrong on processed frames check")

    def multi_process_frame(self, processor: BaseFrameProcessor, frames: Iterable[int], extract: Callable[[int], NumberedFrame], save: Callable[[NumberedFrame], None], progress: tqdm) -> None:  # type: ignore[type-arg]
        def process_done(future_: Future[None]) -> None:
            try:
                futures.remove(future_)
                progress.set_postfix(self.get_postfix(len(futures)))
                progress.update()
            except Exception as E:
                self.update_status(f'process_done() error: {E} ')

        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            futures: list[Future[None]] = []
            try:
                for frame_num in frames:
                    future: Future[None] = executor.submit(self.process_frame, frame_num, extract, processor.process_frame, save)
                    future.add_done_callback(process_done)
                    futures.append(future)
                    progress.set_postfix(self.get_postfix(len(futures)))
                    if get_mem_usage('vms', 'g') >= self.max_memory:
                        futures[:1][0].result()
                        self._statistics['limits_reaches'] += 1
                for completed_future in as_completed(futures):
                    completed_future.result()
            except Exception as E:
                self.update_status(f'multi_process_frame() error: {E} ')

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

    @staticmethod
    def suggest_handler(target_path: str | None, parameters: Namespace) -> BaseFrameHandler:  # todo: refactor this
        if target_path is None:
            raise Exception("The target path is not set")
        if is_dir(target_path):
            return DirectoryHandler(target_path, parameters)
        if is_image(target_path):
            return ImageHandler(target_path, parameters)
        if is_video(target_path):
            return VideoHandler(target_path, parameters)
        raise NotImplementedError("The handler for current target type is not implemented")
