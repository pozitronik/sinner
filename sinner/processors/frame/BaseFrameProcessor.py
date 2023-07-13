import os.path
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Callable, Any, Iterable

import torch
from tqdm import tqdm
from argparse import Namespace

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.validators.AttributeLoader import AttributeLoader, Rules
from sinner.State import State
from sinner.typing import Frame, FramesDataType, FrameDataType, NumeratedFrame
from sinner.utilities import update_status, load_class, get_mem_usage, read_image, suggest_execution_threads, suggest_execution_providers, is_image, is_video


class BaseFrameProcessor(ABC, AttributeLoader):
    target_path: str
    output_path: str
    execution_provider: List[str]  # todo fix execution providers naming (convert from cpu to CPUExecutionProvider
    execution_threads: int

    max_memory: int

    state: State
    extract_frame_method: Callable[[int], NumeratedFrame]
    statistics: dict[str, int] = {'mem_rss_max': 0, 'mem_vms_max': 0, 'limits_reaches': 0}
    progress_callback: Callable[[int], None] | None = None

    parameters: Namespace

    @staticmethod
    def create(processor_name: str, parameters: Namespace, state: State) -> 'BaseFrameProcessor':  # processors factory
        handler_class = load_class(os.path.dirname(__file__), processor_name)

        if handler_class and issubclass(handler_class, BaseFrameProcessor):
            params: dict[str, Any] = {'state': state, 'parameters': parameters}
            return handler_class(**params)
        else:
            raise ValueError(f"Invalid processor name: {processor_name}")

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'max-memory',  # key defined in Parameters
            },
            {
                'parameter': 'execution-provider',
                'required': True,
                'default': ['cpu'],
                'choices': suggest_execution_providers()
            },
            {
                'parameter': 'execution-threads',
                'type': int,
                'default': suggest_execution_threads()
            }
        ]

    def __init__(self, parameters: Namespace, state: State) -> None:
        super().__init__(parameters)
        self.parameters = parameters
        self.state = state

    def get_mem_usage(self) -> str:
        mem_rss = get_mem_usage()
        mem_vms = get_mem_usage('vms')
        if self.statistics['mem_rss_max'] < mem_rss:
            self.statistics['mem_rss_max'] = mem_rss
        if self.statistics['mem_vms_max'] < mem_vms:
            self.statistics['mem_vms_max'] = mem_vms
        return '{:.2f}'.format(mem_rss).zfill(5) + 'MB [MAX:{:.2f}'.format(self.statistics['mem_rss_max']).zfill(5) + 'MB]' + '/' + '{:.2f}'.format(mem_vms).zfill(5) + 'MB [MAX:{:.2f}'.format(
            self.statistics['mem_vms_max']).zfill(5) + 'MB]'

    def process(self, frames_handler: BaseFrameHandler, extract_frames: bool = False, desc: str = 'Processing', set_progress: Callable[[int], None] | None = None) -> None:
        self.extract_frame_method = frames_handler.extract_frame
        self.state._processor_name = self.__class__.__name__
        self.progress_callback = set_progress
        frames_handler.current_frame_index = self.state.processed_frames_count
        # todo: do not create on intermediate directory handler
        frames_list: FramesDataType = frames_handler.get_frames_paths(self.state.in_dir) if extract_frames and isinstance(frames_handler, Iterable) else frames_handler
        if self.state.is_started:
            update_status(f'Temp resources for this target already exists with {self.state.processed_frames_count} frames processed, continue processing...')
        with tqdm(
                total=self.state.frames_count,
                desc=desc, unit='frame',
                dynamic_ncols=True,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
                initial=self.state.processed_frames_count,
        ) as progress:
            self.multi_process_frame(frames_list=frames_list, process_frames=self.process_frames, progress=progress)

    @abstractmethod
    def process_frame(self, temp_frame: Frame) -> Frame:
        pass

    def process_frames(self, frame_data: FrameDataType) -> None:  # type: ignore[type-arg]
        try:
            if isinstance(frame_data, int):
                frame_num, frame = self.extract_frame_method(frame_data)
            else:
                frame = read_image(frame_data[1])
                frame_num = frame_data[0]
            self.state.save_temp_frame(self.process_frame(frame), frame_num)
        except Exception as exception:
            print(exception)
            pass

    def get_postfix(self, futures_length: int) -> dict[str, Any]:
        postfix = {
            'memory_usage': self.get_mem_usage(),
            'futures': futures_length,
        }
        if self.statistics['limits_reaches'] > 0:
            postfix['limit_reaches'] = self.statistics['limits_reaches']
        return postfix

    def multi_process_frame(self, frames_list: FramesDataType, process_frames: Callable[[FrameDataType], None], progress: tqdm) -> None:  # type: ignore[type-arg]
        def process_done(future_: Future[None]) -> None:
            futures.remove(future_)
            progress.set_postfix(self.get_postfix(len(futures)))
            progress.update()
            if self.progress_callback is not None:
                self.progress_callback(progress.n)

        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            futures: list[Future[None]] = []
            for frame in frames_list:
                future: Future[None] = executor.submit(process_frames, frame)
                future.add_done_callback(process_done)
                futures.append(future)
                progress.set_postfix(self.get_postfix(len(futures)))
                if get_mem_usage('vms', 'g') >= self.parameters.max_memory:
                    futures[:1][0].result()
                    self.statistics['limits_reaches'] += 1
            for completed_future in as_completed(futures):
                completed_future.result()

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.execution_provider:
            torch.cuda.empty_cache()

    @abstractmethod
    def suggest_output_path(self) -> str:
        pass
