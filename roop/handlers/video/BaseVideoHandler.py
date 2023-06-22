from abc import ABC, abstractmethod

from roop.typing import Frame


class BaseVideoHandler(ABC):
    fps: float
    fc: int
    _target_path: str

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

    @abstractmethod
    def extract_frames(self, to_dir: str) -> None:
        pass

    @abstractmethod
    def extract_frame(self, frame_number: int) -> Frame:
        pass

    @abstractmethod
    def create_video(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> None:
        pass