import os.path
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Callable, Any, Iterable

import torch
from tqdm import tqdm
from argparse import Namespace

from sinner.Status import Status, Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.validators.AttributeLoader import AttributeLoader, Rules
from sinner.State import State
from sinner.typing import Frame, NumeratedFrame
from sinner.utilities import load_class, get_mem_usage, suggest_execution_threads, suggest_execution_providers, decode_execution_providers, suggest_max_memory


class BaseFrameProcessor(ABC, Status):
    target_path: str
    output_path: str
    execution_provider: List[str]
    execution_threads: int

    max_memory: int

    extract_frame_method: Callable[[int], NumeratedFrame]
    statistics: dict[str, int] = {'mem_rss_max': 0, 'mem_vms_max': 0, 'limits_reaches': 0}
    progress_callback: Callable[[int], None] | None = None

    parameters: Namespace

    @staticmethod
    def create(processor_name: str, parameters: Namespace) -> 'BaseFrameProcessor':  # processors factory
        handler_class = load_class(os.path.dirname(__file__), processor_name)

        if handler_class and issubclass(handler_class, BaseFrameProcessor):
            params: dict[str, Any] = {'parameters': parameters}
            return handler_class(**params)
        else:
            raise ValueError(f"Invalid processor name: {processor_name}")

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'max-memory',  # key defined in Run, but class can be called separately in tests
                'default': suggest_max_memory()
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
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'valid': lambda: os.path.exists(self.target_path),
                'required': True,
                'help': 'Select the target file or the directory'
            },
        ]

    def __init__(self, parameters: Namespace) -> None:
        super().__init__(parameters)
        self.parameters = parameters

    def get_mem_usage(self) -> str:
        mem_rss = get_mem_usage()
        mem_vms = get_mem_usage('vms')
        if self.statistics['mem_rss_max'] < mem_rss:
            self.statistics['mem_rss_max'] = mem_rss
        if self.statistics['mem_vms_max'] < mem_vms:
            self.statistics['mem_vms_max'] = mem_vms
        return '{:.2f}'.format(mem_rss).zfill(5) + 'MB [MAX:{:.2f}'.format(self.statistics['mem_rss_max']).zfill(5) + 'MB]' + '/' + '{:.2f}'.format(mem_vms).zfill(5) + 'MB [MAX:{:.2f}'.format(
            self.statistics['mem_vms_max']).zfill(5) + 'MB]'

    def process(self, frames: BaseFrameHandler, state: State, desc: str = 'Processing', set_progress: Callable[[int], None] | None = None) -> None:
        self.extract_frame_method = frames.extract_frame
        self.progress_callback = set_progress
        frames.current_frame_index = state.processed_frames_count
        # todo: do not create on intermediate directory handler
        with tqdm(
                total=state.frames_count,
                desc=desc, unit='frame',
                dynamic_ncols=True,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
                initial=state.processed_frames_count,
        ) as progress:
            self.multi_process_frame(frames_iterator=frames, state=state, process_frames=self.process_frames, progress=progress)
        if not state.final_check():
            raise Exception("Something went wrong on processed frames check")

    @abstractmethod
    def process_frame(self, frame: Frame) -> Frame:
        pass

    def process_frames(self, frame_num: int, state: State) -> None:  # type: ignore[type-arg]
        try:
            frame_num, frame = self.extract_frame_method(frame_num)
            state.save_temp_frame(self.process_frame(frame), frame_num)
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
        if 'CUDAExecutionProvider' in self.execution_providers:
            torch.cuda.empty_cache()

    @abstractmethod
    def suggest_output_path(self) -> str:
        pass

    @property
    def execution_providers(self) -> List[str]:
        return decode_execution_providers(self.execution_provider)
