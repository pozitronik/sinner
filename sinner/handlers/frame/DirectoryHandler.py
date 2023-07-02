import glob
import os
from typing import List

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.utilities import read_image


class DirectoryHandler(BaseFrameHandler):

    def __init__(self, target_path: str):
        if not os.path.exists(target_path) or not os.path.isdir(target_path):
            raise Exception(f"{target_path} should point to a directory with png images")
        super().__init__(target_path)

    def detect_fps(self) -> float:
        return 1  # todo

    def detect_fc(self) -> int:
        return len(self.get_frames_paths(self._target_path))

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        return [(i + 1, s) for i, s in enumerate(sorted(glob.glob(os.path.join(glob.escape(self._target_path), '*.png'))))]  # todo support any image type

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        return frame_number, read_image(self.get_frames_paths(self._target_path)[frame_number - 1][1])  # zero-based sorted frames list

    def result(self, from_dir: str, filename: str, fps: None | float = None, audio_target: str | None = None) -> bool:
        return False  # Handler can't product any result
