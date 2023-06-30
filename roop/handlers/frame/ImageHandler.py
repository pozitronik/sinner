import os.path
import shutil
from typing import List

from roop.handlers.frame.BaseFrameHandler import BaseFrameHandler
from roop.typing import NumeratedFrame, NumeratedFramePath
from roop.utilities import read_image


class ImageHandler(BaseFrameHandler):

    def detect_fps(self) -> float:
        return 1

    def detect_fc(self) -> int:
        return 1

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        return [(1, self._target_path)]

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        return frame_number, read_image(self._target_path)

    def result(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> bool:
        try:
            shutil.copyfile(os.path.join(from_dir, os.listdir(from_dir).pop()), filename)
            return True
        except Exception:
            pass
            return False
