import glob
import os
from abc import ABC, abstractmethod
from typing import List

from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.utilities import load_class


class BaseFrameHandler(ABC):
    fps: float
    fc: int
    _target_path: str
    current_frame_index: int = 0

    @staticmethod
    def create(handler_name: str, target_path: str) -> 'BaseFrameHandler':  # handlers factory
        handler_class = globals().get(handler_name)
        if not handler_class:
            handler_class = load_class(os.path.dirname(__file__), handler_name)
        if handler_class and issubclass(handler_class, BaseFrameHandler):
            return handler_class(target_path)
        else:
            raise ValueError(f"Invalid handler name: {handler_name}")

    @staticmethod
    def available() -> bool:
        """
        If this handler is available
        """
        return True

    def __init__(self, target_path: str):
        self._target_path = target_path
        self.fps = self.detect_fps()
        self.fc = self.detect_fc()

    @abstractmethod
    def detect_fps(self) -> float:
        pass

    @abstractmethod
    def detect_fc(self) -> int:
        pass

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        """
        Return the list of path for frame in the target.
        Frames should be extracted to `path` if necessary
        """
        return [(i + 1, s) for i, s in enumerate(glob.glob(os.path.join(glob.escape(path), '*.png')))]

    @abstractmethod
    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        """
        Return the certain frame from the target
        """
        pass

    @abstractmethod
    def result(self, from_dir: str, filename: str, fps: None | float = None, audio_target: str | None = None) -> bool:
        """
        Creates a result file from processed frame, return success of operation
        """
        pass

    def __iter__(self) -> 'BaseFrameHandler':
        return self

    def __next__(self) -> int:
        if self.current_frame_index == self.fc:
            raise StopIteration
        self.current_frame_index += 1
        return self.current_frame_index