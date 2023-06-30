import glob
import os
from abc import ABC, abstractmethod
from typing import List

from roop.typing import NumeratedFrame
from roop.utilities import load_class


class BaseFramesHandler(ABC):
    fps: float
    fc: int
    _target_path: str
    current_frame_index: int = 0

    @staticmethod
    def create(handler_name: str, target_path: str) -> 'BaseFramesHandler':  # handlers factory
        handler_class = globals().get(handler_name)
        if not handler_class:
            handler_class = load_class(os.path.dirname(__file__), handler_name)
        if handler_class and issubclass(handler_class, BaseFramesHandler):
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

    def get_frames_paths(self, path: str) -> List[tuple[int, str]]:
        """
        Return the list of path for frames in the target.
        Frames should be extracted to `path` if necessary
        """
        return [(i, s) for i, s in enumerate(glob.glob(os.path.join(glob.escape(path), '*.png')))]

    @abstractmethod
    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        """
        Return the certain frame from the target
        """
        pass

    @abstractmethod
    def result(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> bool:
        """
        Creates a result file from processed frames, return success of operation
        """
        pass

    def __iter__(self) -> 'BaseFramesHandler':
        return self

    def __next__(self) -> tuple[int, Frame]:
        if self.current_frame_index == self.fc:
            raise StopIteration
        index, frame = self.extract_frame(self.current_frame_index)
        self.current_frame_index += 1
        return index, frame
