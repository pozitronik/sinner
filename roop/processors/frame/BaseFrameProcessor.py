from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Iterable

from tqdm import tqdm

from roop.typing import Frame


class BaseFrameProcessor(ABC):
    execution_providers: List[str] = ["CPUExecutionProvider"]
    execution_threads: int = 1
    max_memory: int = 1

    def __init__(self, execution_providers: List[str], execution_threads: int, max_memory: int) -> None:
        self.execution_providers = execution_providers
        self.execution_threads = execution_threads
        self.max_memory = max_memory
        if not self.validate():
            quit()

    @abstractmethod
    def process(self, frames_provider: Iterable[tuple[Frame, int]]) -> None:
        pass

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
