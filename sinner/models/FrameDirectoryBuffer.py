import os
import threading
from bisect import bisect_right
from enum import Enum
from pathlib import Path
from typing import List

from sinner.helpers.FrameHelper import write_to_image, read_from_image
from sinner.models.NumberedFrame import NumberedFrame
from sinner.typing import Frame
from sinner.utilities import is_absolute_path, path_exists, get_file_name


class CacheStrategy(Enum):
    NONE = 0  # use cache only for indices check
    ON_INIT = 1  # cache all existed frames to the memory (very wasteful)
    ON_ADD = 2  # cache only fresh frames (default strategy)


class FrameDirectoryBuffer:
    _temp_dir: str
    _zfill_length: int | None
    _path: str | None = None
    _indices: List[int] = []  # it's required to have a separate frame indices list for quick search of frames
    _frame_cache: dict[int, Frame] = {}

    cache_strategy: CacheStrategy = CacheStrategy.NONE

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
            raise Exception("Relative paths are not supported")
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
        self._frame_cache = {}
        # shutil.rmtree(self._path)

    def add_frame(self, frame: NumberedFrame) -> None:
        with threading.Lock():
            if not write_to_image(frame.frame, self.get_frame_processed_name(frame)):
                raise Exception(f"Error saving frame: {self.get_frame_processed_name(frame)}")
            self._indices.append(frame.index)
            if self.cache_strategy in [CacheStrategy.ON_ADD, CacheStrategy.ON_INIT]:
                self._frame_cache[frame.index] = frame.frame

    def get_frame(self, index: int, return_previous: bool = True) -> NumberedFrame | None:
        cache_result = self.has_frame(index)
        if cache_result is True:  # the frame is on the disk
            filename = str(index).zfill(self.zfill_length) + '.png'
            filepath = str(os.path.join(self.path, filename))
            with threading.Lock():
                try:
                    return NumberedFrame(index, read_from_image(filepath))
                except Exception:
                    pass
        elif cache_result is False:
            if return_previous:
                previous_position = bisect_right(self._indices, index - 1)
                if previous_position > 0:
                    previous_index = self._indices[previous_position - 1]
                    return self.get_frame(previous_index, return_previous=False)
                else:
                    return None
            else:
                return None
        return NumberedFrame(index, cache_result)

    def has_frame(self, index: int) -> bool | Frame:
        """
        :param index: Requested frame index
        :return: Frame if there's in cache, True if frame is on the disk, else return False
        """
        if index in self._indices:
            if index in self._frame_cache.keys():
                return self._frame_cache[index]  # a frame is cached
            return True  # frame on the disk
        return False

    def has_index(self, index: int) -> bool:
        return index in self._indices

    def init_indices(self) -> None:
        with os.scandir(self.path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith(".png"):
                    entry_index = int(get_file_name(entry.name))
                    self._indices.append(entry_index)
                    if self.cache_strategy is CacheStrategy.ON_INIT:
                        self._frame_cache[entry_index] = read_from_image(entry.path)
