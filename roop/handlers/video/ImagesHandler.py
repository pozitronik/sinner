import os.path
import shutil

from roop.handlers.video.BaseVideoHandler import BaseVideoHandler
from roop.typing import Frame
from roop.utilities import read_image


class ImagesHandler(BaseVideoHandler):
    def detect_fps(self) -> float:
        return 1

    def detect_fc(self) -> int:
        return 1

    def extract_frames(self, to_dir: str) -> None:
        pass

    def extract_frame(self, frame_number: int) -> tuple[Frame, int]:
        return read_image(self._target_path), frame_number

    def create_video(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> None:
        shutil.copyfile(os.path.join(from_dir, '0001.png'), filename)
