import glob
import os
import shutil
from argparse import Namespace
from typing import List

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.utilities import is_image, get_file_name, path_exists, is_dir
from sinner.validators.AttributeLoader import Rules


class DirectoryHandler(BaseFrameHandler):
    emoji: str = '📂'

    _fc: int | None = None
    _frames_path: list[str] | None = None

    def rules(self) -> Rules:
        return [
            {
                'module_help': 'The module for processing image files in a directory'
            }
        ]

    def __init__(self, target_path: str, parameters: Namespace):
        if not path_exists(target_path) or not is_dir(target_path):  # todo: move to validator
            raise Exception(f"{target_path} should point to a directory with image files")
        super().__init__(target_path, parameters)

    @property
    def fps(self) -> float:
        return 1  # todo

    @property
    def fc(self) -> int:
        if self._fc is None:
            self._fc = len(list(filter(is_image, glob.glob(os.path.join(glob.escape(self._target_path), '*.*')))))
        return self._fc

    def get_frames_paths(self, path: str, frames_range: tuple[int | None, int | None] = (None, None)) -> List[NumeratedFramePath]:
        if self._frames_path is None:
            self._frames_path = sorted((file_path for file_path in glob.glob(os.path.join(glob.escape(self._target_path), '*.*')) if is_image(file_path)))
        start_frame = frames_range[0] if frames_range[0] is not None else 0
        stop_frame = frames_range[1] + 1 if frames_range[1] is not None else len(self._frames_path)
        return [(frames_index, file_path) for frames_index, file_path in enumerate(self._frames_path)][start_frame:stop_frame]

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        frame_path = self.get_frames_paths(self._target_path, (frame_number, frame_number))[0][1]
        return frame_number, CV2VideoHandler.read_image(frame_path), get_file_name(frame_path)  # zero-based sorted frames list

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        self.update_status(f"Copying results from {from_dir} to {filename}")
        shutil.copytree(from_dir, filename, dirs_exist_ok=True)
        return True  # Handler can't product any result
