import os.path
import shutil
from typing import List

from roop.handlers.frames.BaseFramesHandler import BaseFramesHandler
from roop.typing import Frame
from roop.utilities import read_image


class ImagesHandler(BaseFramesHandler):

    def detect_fps(self) -> float:
        return 1

    def detect_fc(self) -> int:
        return 1

    def get_frames_paths(self, path: str) -> List[str]:
        return [self._target_path]

    def extract_frame(self, frame_number: int) -> tuple[Frame, int]:
        return read_image(self._target_path), frame_number

    def result(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> bool:
        try:
            shutil.copyfile(os.path.join(from_dir, os.listdir(from_dir).pop()), filename)
            return True
        except Exception:
            pass
            return False
