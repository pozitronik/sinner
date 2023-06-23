from abc import ABC, abstractmethod

from roop.typing import Frame


class BaseVideoHandler(ABC):
    fps: float
    fc: int
    _target_path: str
    current_frame_index: int = 0

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
    def extract_frame(self, frame_number: int) -> tuple[Frame, int]:
        pass

    @abstractmethod
    def create_video(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> None:
        pass

    def __iter__(self):
        return self

    def __next__(self) -> tuple[Frame, int]:
        if self.current_frame_index == self.fc:
            raise StopIteration
        frame, index = self.extract_frame(self.current_frame_index)
        self.current_frame_index += 1
        return frame, index
