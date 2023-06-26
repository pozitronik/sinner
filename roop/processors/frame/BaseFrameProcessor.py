from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Iterable

from tqdm import tqdm

from roop.parameters import Parameters
from roop.typing import Frame


class BaseFrameProcessor(ABC):
    execution_providers: List[str] = ["CPUExecutionProvider"]
    execution_threads: int = 1
    max_memory: int = 1

    def __init__(self, params: Parameters) -> None:
        self.execution_providers = params.execution_providers
        self.execution_threads = params.execution_threads
        self.max_memory = params.max_memory
        if not self.validate():
            quit()

    @abstractmethod
    def process(self, frames_provider: Iterable[tuple[Frame, int]]) -> None:
        pass

    def multi_process_frame(self, frames_provider: Iterable[tuple[Frame, int]], process_frames: Callable[[Iterable[tuple[Frame, int]], None | tqdm], None], progress: None | tqdm = None) -> None:
        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            futures = []
            for frame in frames_provider:
                future = executor.submit(process_frames, [frame], progress)
                futures.append(future)
            for future in futures:
                future.result()

    @staticmethod
    def validate() -> bool:
        return True
