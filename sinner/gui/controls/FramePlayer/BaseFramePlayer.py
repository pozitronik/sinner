from abc import abstractmethod

import numpy

from sinner.helpers import FrameHelper
from sinner.typing import Frame

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
HWND_BOTTOM = 1
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOACTIVATE = 0x0010

# those are similar to cv2 constants with same names
ROTATE_90_CLOCKWISE = 0
ROTATE_180 = 1
ROTATE_90_COUNTERCLOCKWISE = 2


class BaseFramePlayer:
    _last_frame: Frame | None = None  # the last viewed frame
    _rotate: int | None = None

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
    def rotate(self) -> int | None:
        return self._rotate

    @rotate.setter
    def rotate(self, value: int | None) -> None:
        self._rotate = value
        if self._last_frame is not None:
            self.clear()
            _tmp_frame = self._last_frame
            self.show_frame(self._last_frame)
            self._last_frame = _tmp_frame

    def _rotate_frame(self, frame: Frame, rotate_mode: int | None = None) -> Frame:
        if rotate_mode is None:
            rotate_mode = self._rotate
        if rotate_mode is None:
            return frame
        if rotate_mode == ROTATE_90_CLOCKWISE:
            return numpy.rot90(frame)
        if rotate_mode is ROTATE_180:
            return numpy.rot90(frame, k=2)
        if rotate_mode == ROTATE_90_COUNTERCLOCKWISE:
            return numpy.rot90(frame, k=3)
        return frame

    @abstractmethod
    def set_fullscreen(self, fullscreen: bool = True) -> None:
        pass

    @abstractmethod
    def set_topmost(self, on_top: bool = True) -> None:
        pass

    @abstractmethod
    def bring_to_front(self) -> None:
        pass
