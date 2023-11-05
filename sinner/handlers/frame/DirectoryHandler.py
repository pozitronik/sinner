import glob
import os
import shutil
from argparse import Namespace
from typing import List

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.EOutOfRange import EOutOfRange
from sinner.helpers.FrameHelper import read_from_image
from sinner.models.NumberedFrame import NumberedFrame
from sinner.typing import NumeratedFramePath
from sinner.utilities import is_image, get_file_name
from sinner.validators.AttributeLoader import Rules


class DirectoryHandler(BaseFrameHandler):
    emoji: str = '📂'

    _fps: float | None
    _fc: int | None
    _resolution: tuple[int, int] | None
    _frames_path: list[str] | None = None

    def rules(self) -> Rules:
        return [
            {
                'module_help': 'The module for processing image files in a directory'
            }
        ]

    def __init__(self, target_path: str, parameters: Namespace, fps: float | None = None, fc: int | None = None, resolution: tuple[int, int] | None = None):
        if not os.path.exists(target_path) or not os.path.isdir(target_path):  # todo: move to validator
            raise Exception(f"{target_path} should point to a directory with image files")
        super().__init__(target_path, parameters)
        self._fps = fps
        self._fc = fc
        self.resolution = resolution

    @property
    def fps(self) -> float:
        return self._fps if self._fps else 1

    @fps.setter
    def fps(self, value: float | None) -> None:
        self._fps = value

    @property
    def fc(self) -> int:
        if self._fc is None:
            image_count = 0
            for file in os.scandir(self._target_path):
                if is_image(file.path):
                    image_count += 1
            self._fc = image_count
        return self._fc

    @fc.setter
    def fc(self, value: int | None) -> None:
        self._fc = value

    @property
    def resolution(self) -> tuple[int, int] | None:
        return self._resolution

    @resolution.setter
    def resolution(self, value: tuple[int, int] | None) -> None:
        self._resolution = value

    def get_frames_paths(self, path: str, frames_range: tuple[int | None, int | None] = (None, None)) -> List[NumeratedFramePath]:
        if self._frames_path is None:
            self._frames_path = sorted((file_path for file_path in glob.glob(os.path.join(glob.escape(self._target_path), '*.*')) if is_image(file_path)))
        start_frame = frames_range[0] if frames_range[0] is not None else 0
        stop_frame = frames_range[1] + 1 if frames_range[1] is not None else len(self._frames_path)
        return [(frames_index, file_path) for frames_index, file_path in enumerate(self._frames_path)][start_frame:stop_frame]

    def extract_frame(self, frame_number: int) -> NumberedFrame:
        if frame_number >= self.fc:
            raise EOutOfRange(frame_number, 0, self.fc-1)
        list_frame = self.get_frames_paths(self._target_path, (frame_number, frame_number))
        frame_path = list_frame[0][1]
        return NumberedFrame(frame_number, read_from_image(frame_path), get_file_name(frame_path))  # zero-based sorted frames list

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        self.update_status(f"Copying results from {from_dir} to {filename}")
        shutil.copytree(from_dir, filename, dirs_exist_ok=True)
        return True  # Handler can't product any result
