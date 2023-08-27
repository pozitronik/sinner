import os.path
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from threading import Thread
from typing import List, Callable, Any, Iterable, Dict

from tqdm import tqdm
from argparse import Namespace

from sinner.Status import Status, Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.validators.AttributeLoader import Rules
from sinner.State import State
from sinner.typing import Frame, FrameBuffer, NumeratedFrame
from sinner.utilities import load_class, get_mem_usage, suggest_execution_threads, suggest_execution_providers, decode_execution_providers, suggest_max_memory, is_image, is_video, get_app_dir, TEMP_DIRECTORY


class BaseFrameProcessor(ABC, Status):
    target_path: str
    output_path: str
    execution_provider: List[str]
    execution_threads: int
    temp_dir: str

    max_memory: int

    statistics: dict[str, int] = {'mem_rss_max': 0, 'mem_vms_max': 0, 'limits_reaches': 0}
    progress_callback: Callable[[int], None] | None = None

    parameters: Namespace
    state: State
    handler: BaseFrameHandler

    @staticmethod
    def create(processor_name: str, parameters: Namespace, target_path: str | None = None) -> 'BaseFrameProcessor':  # processors factory
        handler_class = load_class(os.path.dirname(__file__), processor_name)

        if handler_class and issubclass(handler_class, BaseFrameProcessor):
            params: dict[str, Any] = {'parameters': parameters, 'target_path': target_path}
            return handler_class(**params)
        else:
            raise ValueError(f"Invalid processor name: {processor_name}")

    def suggest_temp_dir(self) -> str:
        return self.temp_dir if self.temp_dir is not None else os.path.join(get_app_dir(), TEMP_DIRECTORY)

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'max-memory',  # key defined in Sin, but class can be called separately in tests
                'default': suggest_max_memory(),
            },
            {
                'parameter': 'execution-provider',
                'required': True,
                'default': ['cpu'],
                'choices': suggest_execution_providers(),
                'help': 'The execution provider, from available on your hardware/software'
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
                'valid': lambda: os.path.exists(self.target_path),
                'required': True,
                'help': 'Select the target file or the directory'
            },
            {
                'parameter': 'temp-dir',
                'default': lambda: self.suggest_temp_dir(),
                'help': 'Select the directory for temporary files'
            },
        ]

    def __init__(self, parameters: Namespace, target_path: str | None = None) -> None:
        self.parameters = parameters
        super().__init__(self.parameters)
        if target_path is None:
            target_path = self.target_path

        self.handler = self.suggest_handler(target_path, self.parameters)
        self.state = State(parameters=self.parameters, target_path=target_path, temp_dir=self.temp_dir, frames_count=self.handler.fc, processor_name=self.__class__.__name__)

    def get_mem_usage(self) -> str:
        mem_rss = get_mem_usage()
        mem_vms = get_mem_usage('vms')
        if self.statistics['mem_rss_max'] < mem_rss:
            self.statistics['mem_rss_max'] = mem_rss
        if self.statistics['mem_vms_max'] < mem_vms:
            self.statistics['mem_vms_max'] = mem_vms
        return '{:.2f}'.format(mem_rss).zfill(5) + 'MB [MAX:{:.2f}'.format(self.statistics['mem_rss_max']).zfill(5) + 'MB]' + '/' + '{:.2f}'.format(mem_vms).zfill(5) + 'MB [MAX:{:.2f}'.format(
            self.statistics['mem_vms_max']).zfill(5) + 'MB]'

    def fill_initial_buffer(self, shared_buffer: FrameBuffer) -> None:
        for frame_num in self.handler:
            frame = self.handler.extract_frame(frame_num)
            self.update_status(f'Write frame {frame_num} to initial buffer')
            shared_buffer.append(frame)

    def process_buffered(self, buffers: Dict[str, FrameBuffer], name: str | None, next_name: str | None):
        processed_frames_count = 0

        def process_done(future_: Future[None]) -> None:
            futures.remove(future_)

        def process_to_buffer(frame_: NumeratedFrame | None) -> None:
            frame = frame_[0], self.process_frame(frame_[1]), frame_[2]
            if next_name is not None:
                self.update_status(f'Write frame {frame[0]} to output buffer')
                buffers[next_name].append(frame)
            else:
                self.update_status(f'Write frame {frame[0]} to dir')
                self.state.save_temp_frame(frame)

        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            futures: list[Future[None]] = []
            while processed_frames_count < self.handler.fc:
                if len(buffers[name]) > 0:
                    current_frame = buffers[name].pop()
                    future: Future[None] = executor.submit(process_to_buffer, current_frame)
                    future.add_done_callback(process_done)
                    futures.append(future)
                for completed_future in as_completed(futures):
                    completed_future.result()
                    processed_frames_count += 1

    def process(self, desc: str = 'Processing', set_progress: Callable[[int], None] | None = None) -> None:
        self.progress_callback = set_progress
        self.handler.current_frame_index = self.state.processed_frames_count
        # todo: do not create on intermediate directory handler
        with tqdm(
                total=self.state.frames_count,
                desc=desc, unit='frame',
                dynamic_ncols=True,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
                initial=self.state.processed_frames_count,
        ) as progress:
            self.multi_process_frame(frames_iterator=self.handler, state=self.state, process_frames=self.process_frames, progress=progress)
        _, lost_frames = self.state.final_check()
        if lost_frames:
            with tqdm(
                    total=len(lost_frames),
                    desc="Processing lost frames", unit='frame',
                    dynamic_ncols=True,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
            ) as progress:
                self.multi_process_frame(frames_iterator=lost_frames, state=self.state, process_frames=self.process_frames, progress=progress)
        is_ok, _ = self.state.final_check()
        if not is_ok:
            raise Exception("Something went wrong on processed frames check")

    @abstractmethod
    def process_frame(self, frame: Frame) -> Frame:
        pass

    def process_frames(self, frame_num: int, state: State) -> None:  # type: ignore[type-arg]
        try:
            frame = self.handler.extract_frame(frame_num)
            state.save_temp_frame((frame[0], self.process_frame(frame[1]), frame[2]))
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            quit()

    def get_postfix(self, futures_length: int) -> dict[str, Any]:
        postfix = {
            'memory_usage': self.get_mem_usage(),
            'futures': futures_length,
        }
        if self.statistics['limits_reaches'] > 0:
            postfix['limit_reaches'] = self.statistics['limits_reaches']
        return postfix

    def multi_process_frame(self, frames_iterator: Iterable[int], state: State, process_frames: Callable[[int, State], None], progress: tqdm) -> None:  # type: ignore[type-arg]
        def process_done(future_: Future[None]) -> None:
            futures.remove(future_)
            progress.set_postfix(self.get_postfix(len(futures)))
            progress.update()
            if self.progress_callback is not None:
                self.progress_callback(progress.n)

        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            futures: list[Future[None]] = []
            for frame in frames_iterator:
                future: Future[None] = executor.submit(process_frames, frame, state)
                future.add_done_callback(process_done)
                futures.append(future)
                progress.set_postfix(self.get_postfix(len(futures)))
                if get_mem_usage('vms', 'g') >= self.max_memory:
                    futures[:1][0].result()
                    self.statistics['limits_reaches'] += 1
            for completed_future in as_completed(futures):
                completed_future.result()

    def release_resources(self) -> None:
        pass

    @abstractmethod
    def suggest_output_path(self) -> str:
        pass

    @property
    def execution_providers(self) -> List[str]:
        return decode_execution_providers(self.execution_provider)

    @staticmethod
    def suggest_handler(target_path: str | None, parameters: Namespace) -> BaseFrameHandler:
        if target_path is None:
            raise Exception("The target path is not set")
        if os.path.isdir(target_path):
            return DirectoryHandler(target_path, parameters)
        if is_image(target_path):
            return ImageHandler(target_path, parameters)
        if is_video(target_path):
            return VideoHandler(target_path, parameters)
        raise NotImplementedError("The handler for current target type is not implemented")
