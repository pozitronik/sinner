from roop.handlers.frames.BaseFramesHandler import BaseFramesHandler
from roop.typing import Frame
from roop.utilities import read_image


class DirectoryHandler(BaseFramesHandler):

    def __init__(self, target_path: str):
        super().__init__(target_path)
        self.frame_list = self.get_frames_paths(target_path)

    def detect_fps(self) -> float:
        return 1  # todo

    def detect_fc(self) -> int:
        return len(self.frame_list)

    def extract_frame(self, frame_number: int) -> tuple[Frame, int]:
        return read_image(self.frame_list[frame_number]), frame_number

    def result(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> bool:
        try:
            return True
        except Exception:
            pass
            return False
