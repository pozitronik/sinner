import platform
from abc import ABC, abstractmethod
from typing import List, Callable, Any

from concurrent.futures import ThreadPoolExecutor

import cv2
from numpy import array, uint8, fromfile

from roop.parameters import Parameters


class BaseFrameProcessor(ABC):
    source: [None, str, List[str]] = None  # none | file path | list of files

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
    def process(self):
        pass

    def multi_process_frame(self, source_path: str, temp_frame_paths: List[str], process_frames: Callable[[str, List[str], Any], None], progress: Any = None) -> None:
        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            futures = []
            for path in temp_frame_paths:
                future = executor.submit(process_frames, source_path, [path], progress)
                futures.append(future)
            for future in futures:
                future.result()

    @abstractmethod
    def validate(self):
        pass

    def read_image(self, path: str) -> array:
        if platform.system().lower() == 'windows':  # issue #511
            return cv2.imdecode(fromfile(path, dtype=uint8), cv2.IMREAD_UNCHANGED)
        else:
            return cv2.imread(path)


    def write_image(self, image: array, path: str) -> bool:
        if platform.system().lower() == 'windows':  # issue #511
            is_success, im_buf_arr = cv2.imencode(".png", image)
            im_buf_arr.tofile(path)
            return is_success
        else:
            return cv2.imwrite(path, array)