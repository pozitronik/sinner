import inspect
import os.path
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Iterable, Any

from tqdm import tqdm

from roop.parameters import Parameters
from roop.state import State
from roop.typing import Frame
from roop.utilities import get_mem_usage, update_status, write_image, load_class


class BaseFrameProcessor(ABC):
    state: State
    execution_providers: List[str] = ["CPUExecutionProvider"]
    execution_threads: int = 1

    @staticmethod
    def create(processors_name: List[str], parameters: Parameters, state: State) -> List['BaseFrameProcessor']:  # processors factory
        result: List['BaseFrameProcessor'] = []
        for processor_name in processors_name:
            handler_class = load_class(os.path.dirname(__file__), processor_name)

            if handler_class and issubclass(handler_class, BaseFrameProcessor):
                class_parameters_list = inspect.signature(handler_class.__init__).parameters
                params: dict[str, Any] = {}
                for parameter_name in class_parameters_list.keys():
                    if hasattr(parameters, parameter_name):
                        params[parameter_name] = getattr(parameters, parameter_name)
                params['state'] = state
                result.append(handler_class(**params))
            else:
                raise ValueError(f"Invalid processor name: {processor_name}")
        return result

    def __init__(self, execution_providers: List[str], execution_threads: int, state: State) -> None:
        self.execution_providers = execution_providers
        self.execution_threads = execution_threads
        self.state = state
        if not self.validate():
            quit()

    def process(self, frames_provider: Iterable[tuple[Frame, int]], desc: str = 'Processing') -> None:
        if self.state.is_started():
            update_status(f'Temp resources for this target already exists with {self.state.processed_frames_count()} frames processed, continue processing...')
        progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
        with tqdm(total=self.state.frames_count, desc=desc, unit='frame', dynamic_ncols=True, bar_format=progress_bar_format, initial=self.state.processed_frames_count()) as progress:
            progress.set_postfix({
                'memory_usage': '{:.2f}'.format(get_mem_usage()).zfill(5) + 'MB',
                'execution_providers': self.execution_providers,
                'threads': self.execution_threads,
            })
            self.multi_process_frame(frames_provider, self.process_frames, progress)

    @abstractmethod
    def process_frame(self, temp_frame: Frame) -> Frame:
        pass

    def process_frames(self, frames: Iterable[tuple[Frame, int]], progress: None | tqdm = None) -> None:  # type: ignore[type-arg]
        for frame in frames:
            try:
                write_image(self.process_frame(frame[0]), self.state.get_frame_processed_name(frame[1]))
            except Exception as exception:
                print(exception)
                pass
            if progress is not None:
                progress.update()

    def multi_process_frame(self, frames_provider: Iterable[tuple[Frame, int]], process_frames: Callable[[Iterable[tuple[Frame, int]], None | tqdm], None], progress: None | tqdm = None) -> None:  # type: ignore[type-arg]
        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            futures = []
            for frame in frames_provider:
                future = executor.submit(process_frames, [frame], progress)
                futures.append(future)
            for future in as_completed(futures):
                future.result()

    @staticmethod
    def validate() -> bool:
        return True
