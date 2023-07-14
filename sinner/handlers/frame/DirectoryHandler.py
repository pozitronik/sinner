import glob
import os
import shutil
from argparse import Namespace
from typing import List

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.utilities import read_image, is_image, get_file_name


class DirectoryHandler(BaseFrameHandler):

    def __init__(self, target_path: str, parameters: Namespace):
        if not os.path.exists(target_path) or not os.path.isdir(target_path):  # todo: move to validator
            raise Exception(f"{target_path} should point to a directory with image files")
        super().__init__(target_path, parameters)

    def detect_fps(self) -> float:
        return 1  # todo

    def detect_fc(self) -> int:
        return len(glob.glob(os.path.join(glob.escape(self._target_path), '*.*')))

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        frames_path = sorted(glob.glob(os.path.join(glob.escape(self._target_path), '*.*')))
        return [(int(get_file_name(file_path)), file_path) for file_path in frames_path if is_image(file_path)]

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        return frame_number, read_image(self.get_frames_paths(self._target_path)[frame_number - 1][1])  # zero-based sorted frames list

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        self.update_status(f"Copying results from {from_dir} to {filename}")
        shutil.copytree(from_dir, filename, dirs_exist_ok=True)
        return True  # Handler can't product any result
