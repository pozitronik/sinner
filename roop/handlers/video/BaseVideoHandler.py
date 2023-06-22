from abc import ABC, abstractmethod

class BaseVideoHandler(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def detect_fps(self) -> float:
        pass

    @abstractmethod
    def extract_frames(self, to_dir: str) -> None:
        pass

    @abstractmethod
    def extract_frame(self, frame_number: int, to_dir: str) -> str:
        pass

    @abstractmethod
    def create_video(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> None:
        pass