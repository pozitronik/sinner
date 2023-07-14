import glob
import os
from abc import ABC, abstractmethod
from argparse import Namespace
from typing import List

from sinner.validators.AttributeLoader import AttributeLoader, Rules
from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.utilities import load_class, get_file_name


class BaseFrameHandler(AttributeLoader, ABC):
    fps: float
    fc: int
    current_frame_index: int = 0

    _target_path: str

    def rules(self) -> Rules:
        return [
        ]

    @staticmethod
    def create(handler_name: str, target_path: str, parameters: Namespace | None = None) -> 'BaseFrameHandler':  # handlers factory
        handler_class = globals().get(handler_name)
        if not handler_class:
            handler_class = load_class(os.path.dirname(__file__), handler_name)
        if handler_class and issubclass(handler_class, BaseFrameHandler):
            return handler_class(target_path, parameters)
        else:
            raise ValueError(f"Invalid handler name: {handler_name}")

    @staticmethod
    def available() -> bool:
        """
        If this handler is available
        """
        return True

    def __init__(self, target_path: str, parameters: Namespace | None = None):
        self._target_path = target_path
        self.fps = self.detect_fps()
        self.fc = self.detect_fc()
        super().__init__(parameters)

    @abstractmethod
    def detect_fps(self) -> float:
        pass

    @abstractmethod
    def detect_fc(self) -> int:
        pass

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        frames_path = sorted(glob.glob(os.path.join(glob.escape(path), '*.png')))
        return [(int(get_file_name(file_path)), file_path) for file_path in frames_path]

    @abstractmethod
    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        """
        Return the certain frame from the target
        """
        pass

    @abstractmethod
    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        """
        Creates a result file from processed frame, return success of operation
        """
        pass

    def __iter__(self) -> 'BaseFrameHandler':
        return self

    def __next__(self) -> int:
        if self.current_frame_index >= self.fc:
            raise StopIteration
        self.current_frame_index += 1
        return self.current_frame_index
