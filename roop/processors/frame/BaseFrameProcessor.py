from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Iterable

from tqdm import tqdm

from roop.parameters import Parameters


class BaseFrameProcessor(ABC):
    FT_PATH = 1
    FT_FRAME_TUPLE = 2

    source: None | str | List[str] = None  # none | file path | list of files

    execution_providers: List[str] = ["CPUExecutionProvider"]
    execution_threads: int = 1
    max_memory: int = 1

    def __init__(self, params: Parameters):
        self.source = params.source_path
        self.target = params.target_path
        self.execution_providers = params.execution_providers
        self.execution_threads = params.execution_threads
        self.max_memory = params.max_memory
        if not self.validate(): quit()

    @abstractmethod
    def process(self, frames_provider: Iterable):
        pass

    def multi_process_frame(self, frames_provider: Iterable, process_frames: Callable[[Iterable, None | tqdm], None], progress: None | tqdm = None) -> None:
        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            futures = []
            for frame in frames_provider:
                future = executor.submit(process_frames, [frame], progress)
                futures.append(future)
            for future in futures:
                future.result()

    @abstractmethod
    def validate(self):
        pass