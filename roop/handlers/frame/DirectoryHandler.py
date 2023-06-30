import glob
import os
from typing import List

from roop.handlers.frame.BaseFrameHandler import BaseFrameHandler
from roop.typing import NumeratedFrame, NumeratedFramePath
from roop.utilities import read_image


class DirectoryHandler(BaseFrameHandler):

    def __init__(self, target_path: str):
        super().__init__(target_path)

    def detect_fps(self) -> float:
        return 1  # todo

    def detect_fc(self) -> int:
        return len(self.get_frames_paths(self._target_path))

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        """
        Return the list of path for frame in the target.
        Frames should be extracted to `path` if necessary
        """
        return [(i, s) for i, s in enumerate(glob.glob(os.path.join(glob.escape(self._target_path), '*.png')))]

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        return frame_number, read_image(self.get_frames_paths(self._target_path)[frame_number][1])

    def result(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> bool:
        try:
            return True
        except Exception:
            pass
            return False
