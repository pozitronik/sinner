import glob
import os
from abc import ABC, abstractmethod
from argparse import Namespace
from typing import List

from sinner.Status import Status
from sinner.models.NumberedFrame import NumberedFrame
from sinner.validators.AttributeLoader import Rules
from sinner.typing import NumeratedFramePath
from sinner.utilities import load_class, get_file_name


class BaseFrameHandler(Status, ABC):
    current_frame_index: int = 0

    _target_path: str
    _fps: float | None = None
    _fc: int | None = None
    _resolution: tuple[int, int] | None = None
    _length: float | None = None

    def rules(self) -> Rules:
        return [
        ]

    @staticmethod
    def create(handler_name: str, target_path: str, parameters: Namespace) -> 'BaseFrameHandler':  # handlers factory
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

    def __init__(self, target_path: str, parameters: Namespace):
        self._target_path = target_path
        super().__init__(parameters)
        self.update_status(f"Handle frames for {self._target_path} ({self.fc} frame(s)/{self.fps} FPS)")

    @property
    @abstractmethod
    def fps(self) -> float:
        pass

    @property
    @abstractmethod
    def fc(self) -> int:
        pass

    @property
    def frame_time(self) -> float:
        return 1 / self.fps

    @property
    @abstractmethod
    def resolution(self) -> tuple[int, int]:
        """
        Returns the target dimension resolution (WxH) if present, else (0, 0)
        """
        pass

    @property
    def length(self) -> float:
        """
        Returns the target play length in seconds if it can be determined, else None
        """
        if self._length is None:
            self._length = self.fc / self.fps
        return self._length

    def get_frames_paths(self, path: str, frames_range: tuple[int | None, int | None] = (None, None)) -> List[NumeratedFramePath]:
        """
        Returns all frames paths (extracting them into files, if needed). File names starting from zero index
        :param path: the frames directory
        :param frames_range: sets the range of returned (and extracted) frames
        :return: list of requested frames
        """
        frames_path = sorted(glob.glob(os.path.join(glob.escape(path), '*.png')))
        return [(int(get_file_name(file_path)), file_path) for file_path in frames_path if os.path.isfile(file_path)][frames_range[0]:frames_range[1]]

    @abstractmethod
    def extract_frame(self, frame_number: int) -> NumberedFrame:
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
        return self.current_frame_index - 1  # zero-based
