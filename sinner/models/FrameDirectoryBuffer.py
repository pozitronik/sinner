import os
import shutil
import threading
from pathlib import Path

from sinner.helpers.FrameHelper import write_to_image, read_from_image
from sinner.models.NumberedFrame import NumberedFrame
from sinner.utilities import is_absolute_path, path_exists


# Internal class, used to implement extracted frames buffering
# Was a part of experiment of frame processing acceleration
# Currently isn't used.
class FrameDirectoryBuffer():
    _temp_dir: str
    _zfill_length: int | None
    _path: str | None = None

    def __init__(self, file_name: str, temp_dir: str, frames_count: int):
        self.file_name = file_name
        self.temp_dir = temp_dir
        self.frames_count = frames_count
        self._zfill_length = None

    @property
    def temp_dir(self) -> str:
        return self._temp_dir

    @temp_dir.setter
    def temp_dir(self, value: str | None) -> None:
        if not is_absolute_path(value or ''):
            raise Exception("Relative paths is not supported")
        self._temp_dir = os.path.abspath(os.path.normpath(value or ''))

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
        """
        Processors may not need the source or (in theory) the target. Method tries to configure a part of state path
        for any situation
        :return: adapted state path
        """
        if self._path is None:
            target_path = os.path.basename(self.file_name or '')
            sub_path = (target_path, os.path.basename(self.file_name or ''))
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
        shutil.rmtree(self._path)

    def add_frame(self, frame: NumberedFrame) -> None:
        with threading.Lock():
            if not write_to_image(frame.frame, self.get_frame_processed_name(frame)):
                raise Exception(f"Error saving frame: {self.get_frame_processed_name(frame)}")

    def get_frame(self, index: int) -> NumberedFrame | None:
        frame = None
        filename = str(frame.index).zfill(self.zfill_length) + '.png'
        filepath = str(os.path.join(self.path, filename))
        if Path.exists(filepath):
            frame = index, read_from_image(filepath)
        return frame
