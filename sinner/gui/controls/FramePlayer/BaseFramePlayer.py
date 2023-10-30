import time
from abc import abstractmethod

from sinner.models.PerfCounter import PerfCounter
from sinner.typing import Frame


class BasePlayer:
    _last_frame: Frame | None = None  # the last viewed frame

    @abstractmethod
    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True) -> None:
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
