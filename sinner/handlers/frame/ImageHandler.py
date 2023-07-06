import os.path
import shutil
from pathlib import Path
from typing import List

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.utilities import read_image, is_image


class ImageHandler(BaseFrameHandler):

    def __init__(self, target_path: str):
        if not os.path.exists(target_path) or not os.path.isfile(target_path) or not is_image(target_path):
            raise Exception(f"{target_path} should point to a image file")
        super().__init__(target_path)

    def detect_fps(self) -> float:
        return 1

    def detect_fc(self) -> int:
        return 1

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        return [(1, self._target_path)]

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        return frame_number, read_image(self._target_path)

    def result(self, from_dir: str, filename: str, fps: None | float = None, audio_target: str | None = None) -> bool:
        try:
            Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
            # fixme: there can by other files in the from_dir
            shutil.copyfile(os.path.join(from_dir, os.listdir(from_dir).pop()), filename)
            return True
        except Exception:
            pass
            return False
