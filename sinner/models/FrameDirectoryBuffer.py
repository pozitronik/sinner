import os
import threading
from pathlib import Path
from typing import List

from sinner.helpers.FrameHelper import write_to_image, read_from_image
from sinner.models.NumberedFrame import NumberedFrame
from sinner.utilities import is_absolute_path, path_exists, get_file_name


class FrameDirectoryBuffer:
    _temp_dir: str
    _zfill_length: int | None
    _path: str | None = None
    _indices: List[int] = []

    def __init__(self, source_name: str, target_name: str, temp_dir: str, frames_count: int):
        self.source_name = source_name
        self.target_name = target_name
        self.temp_dir = temp_dir
        self.frames_count = frames_count
        self._zfill_length = None
        self.init_indices()

    @property
    def temp_dir(self) -> str:
        return self._temp_dir

    @temp_dir.setter
    def temp_dir(self, value: str | None) -> None:
        if not is_absolute_path(value or ''):
            raise Exception("Relative paths is not supported")
        self._temp_dir = os.path.abspath(os.path.join(os.path.normpath(value or ''), 'preview'))

    @property
    def zfill_length(self) -> int:
        if self._zfill_length is None:
            self._zfill_length = len(str(self.frames_count))
        return self._zfill_length

    @staticmethod
    def make_path(path: str) -> str:
        if not path_exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

    @property
    def path(self) -> str:
        if self._path is None:
            sub_path = (os.path.basename(self.target_name or ''), os.path.basename(self.source_name or ''))
            self._path = os.path.abspath(os.path.join(self.temp_dir, *sub_path))
            self.make_path(self._path)
        return self._path

    #  Returns a processed file name for an unprocessed frame index
    def get_frame_processed_name(self, frame: NumberedFrame) -> str:
        if frame.name:
            filename = frame.name + '.png'
        else:
            filename = str(frame.index).zfill(self.zfill_length) + '.png'
        return str(os.path.join(self.path, filename))

    def clean(self) -> None:
        pass
        # shutil.rmtree(self._path)

    def add_frame(self, frame: NumberedFrame) -> None:
        with threading.Lock():
            if not write_to_image(frame.frame, self.get_frame_processed_name(frame)):
                raise Exception(f"Error saving frame: {self.get_frame_processed_name(frame)}")
            self._indices.append(frame.index)

    def get_frame(self, index: int, return_previous: bool = True) -> NumberedFrame | None:
        filename = str(index).zfill(self.zfill_length) + '.png'
        filepath = str(os.path.join(self.path, filename))
        if path_exists(filepath):
            return NumberedFrame(index, read_from_image(filepath))
        elif return_previous:
            for previous_number in range(index - 1, 0, -1):
                if self.has_frame(previous_number):
                    previous_filename = str(previous_number).zfill(self.zfill_length) + '.png'
                    previous_file_path = os.path.join(self.path, previous_filename)
                    if path_exists(previous_file_path):
                        return NumberedFrame(index, read_from_image(previous_file_path))
        return None

    def has_frame(self, index: int) -> bool:
        return index in self._indices

    def init_indices(self) -> None:
        with os.scandir(self.path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith(".png"):
                    self._indices.append(int(get_file_name(entry.name)))
