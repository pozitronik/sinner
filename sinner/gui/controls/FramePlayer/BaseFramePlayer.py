import time
from abc import abstractmethod
from enum import Enum

import numpy

from sinner.helpers import FrameHelper
from sinner.models.PerfCounter import PerfCounter
from sinner.typing import Frame

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
HWND_BOTTOM = 1
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOACTIVATE = 0x0010


class RotateMode(Enum):
    ROTATE_0 = "0°"
    ROTATE_90 = "90°"
    ROTATE_180 = "180°"
    ROTATE_270 = "270°"

    def __str__(self) -> str:
        return self.value[1]

    def prev(self) -> 'RotateMode':
        enum_list = list(RotateMode)
        current_index = enum_list.index(self)
        previous_index = (current_index - 1) % len(enum_list)
        return enum_list[previous_index]

    def next(self) -> 'RotateMode':
        enum_list = list(RotateMode)
        current_index = enum_list.index(self)
        next_index = (current_index + 1) % len(enum_list)
        return enum_list[next_index]


class BaseFramePlayer:
    _last_frame: Frame | None = None  # the last viewed frame
    _rotate: RotateMode = RotateMode.ROTATE_0

    @abstractmethod
    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True, rotate: bool = True) -> None:
        """
        Display frame in the player
        :param frame: the frame
        :param resize: True: resize the frame proportionally to fit the current player,
                       False: resize the player to the frame size,
                       tuple[HEIGHT, WIDTH]: resize the frame proportionally to fit in the height and the width,
                       None: do not resize the frame or the player
        :param rotate: True: rotate frame to the current RotateMode, False: do not rotate
        """
        pass

    def show_frame_wait(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True, rotate: bool = True, duration: float = 0) -> float:
        """
        Shows a frame for the given duration (awaits after frame being shown). If duration is lesser than the frame show time
        function won't wait
        :returns await time
        """
        with PerfCounter() as timer:
            self.show_frame(frame=frame, resize=resize, rotate=rotate)
        await_time = duration - timer.execution_time
        if await_time > 0:
            time.sleep(await_time)
        return await_time

    @abstractmethod
    def adjust_size(self, redraw: bool = True, size: tuple[int, int] | None = None) -> None:
        pass

    def save_to_file(self, save_file: str) -> None:
        if self._last_frame is not None:
            FrameHelper.write_to_image(self._last_frame, save_file)

    @abstractmethod
    def clear(self) -> None:
        pass

    @property
    def rotate(self) -> RotateMode:
        return self._rotate

    @rotate.setter
    def rotate(self, value: RotateMode) -> None:
        self._rotate = value
        self.clear()
        if self._last_frame is not None:
            _tmp_frame = self._last_frame
            self.show_frame(self._rotate_frame(self._last_frame), rotate=False)
            self._last_frame = _tmp_frame

    def _rotate_frame(self, frame: Frame, rotate_mode: RotateMode | None = None) -> Frame:
        if rotate_mode is None:
            rotate_mode = self._rotate
        if rotate_mode is RotateMode.ROTATE_0:
            return frame
        if rotate_mode is RotateMode.ROTATE_90:
            return numpy.rot90(frame)
        if rotate_mode is RotateMode.ROTATE_180:
            return numpy.rot90(numpy.rot90(frame))
        if rotate_mode is RotateMode.ROTATE_270:
            return numpy.rot90(numpy.rot90(numpy.rot90(frame)))

    @abstractmethod
    def set_fullscreen(self, fullscreen: bool = True) -> None:
        pass

    @abstractmethod
    def set_topmost(self, on_top: bool = True) -> None:
        pass

    @abstractmethod
    def bring_to_front(self) -> None:
        pass
