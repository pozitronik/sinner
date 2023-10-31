import time
from abc import abstractmethod

from sinner.helpers import FrameHelper
from sinner.models.PerfCounter import PerfCounter
from sinner.typing import Frame


class BaseFramePlayer:
    _last_frame: Frame | None = None  # the last viewed frame

    @abstractmethod
    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True) -> None:
        """
        Display frame in the player
        :param frame: the frame
        :param resize: True: resize the frame proportionally to fit the current player,
                       False: resize the player to the frame size,
                       tuple[HEIGHT, WIDTH]: resize the frame proportionally to fit in the height and the width,
                       None: do not resize the frame or the player
        """
        pass

    def show_frame_wait(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True, duration: float = 0) -> float:
        """
        Shows a frame for the given duration (awaits after frame being shown). If duration is lesser than the frame show time
        function won't wait
        :returns await time
        """
        with PerfCounter() as timer:
            self.show_frame(frame=frame, resize=resize)
        await_time = duration - timer.execution_time
        if await_time > 0:
            time.sleep(await_time)
        return await_time

    @abstractmethod
    def adjust_size(self) -> None:
        pass

    def save_to_file(self, save_file: str) -> None:
        if self._last_frame is not None:
            FrameHelper.write_to_image(self._last_frame, save_file)
