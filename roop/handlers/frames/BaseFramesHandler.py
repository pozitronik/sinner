import glob
import os
from abc import ABC, abstractmethod
from typing import List

from roop.typing import Frame


class BaseFramesHandler(ABC):
    fps: float
    fc: int
    _target_path: str
    current_frame_index: int = 0

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

    def get_frames_paths(self, to_dir: str) -> List[str]:
        """
        Return the list of path for frames in the target.
        Frames should be extracted to `to_dir` if necessary
        """
        return glob.glob(os.path.join(glob.escape(to_dir), '*.png'))

    @abstractmethod
    def extract_frame(self, frame_number: int) -> tuple[Frame, int]:
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

    def __next__(self) -> tuple[Frame, int]:
        if self.current_frame_index == self.fc:
            raise StopIteration
        frame, index = self.extract_frame(self.current_frame_index)
        self.current_frame_index += 1
        return frame, index
