import threading
import time
from typing import Dict

from sinner.models.NumberedFrame import NumberedFrame


class FrameTimeLine:
    _frames: Dict[int, NumberedFrame] = {}
    _timer: float = 0
    _frame_time: float
    _start_frame_index: int
    _end_frame_index: int
    _start_frame_time: float = 0

    _is_started: bool
    _last_written_index: int = 0
    _last_requested_index: int = 0
    _last_returned_index: int | None = None

    def __init__(self, frame_time: float = 0, start_frame: int = 0, end_frame: int = 0):
        self.reload(frame_time, start_frame, end_frame)
        self._is_started = False
        self._frames = {}

    def reload(self, frame_time: float, start_frame: int, end_frame: int) -> None:
        self._frame_time = frame_time
        self._start_frame_index = start_frame
        self._end_frame_index = end_frame
        self._start_frame_time = start_frame * frame_time

    # start the time counter
    def start(self) -> None:
        self._timer = time.perf_counter()
        self._is_started = True

    def stop(self) -> None:
        self._is_started = False
        self._frames = {}

    # returns time passed from the start
    def time(self) -> float:
        return time.perf_counter() - self._timer

    def time_position(self) -> float:
        return self.time() + self._start_frame_time

    def has_frame(self, index: int) -> bool:
        return index in self._frames

    def add_frame(self, frame: NumberedFrame) -> int:
        with threading.Lock():
            self._frames[frame.index] = frame
            if frame.index > self._last_written_index:
                self._last_written_index = frame.index
        return len(self._frames)

    # return the frame at current time position, or None, if there's no frame
    def get_frame(self) -> NumberedFrame | None:
        if not self._is_started:
            self.start()
        self._last_returned_index = self.get_frame_index()
        if self._last_requested_index > self._end_frame_index:
            raise EOFError()

        return self._frames[self._last_returned_index] if self._last_returned_index else None

    # naive stub
    def last_index_before(self, index: int) -> int | None:
        indices = list(reversed(self._frames.keys()))
        for current_index in indices:
            if current_index <= index:
                return current_index
        return None

    # return the index of a frame, is playing right now if it is in self._frames
    # else return last frame before requested
    def get_frame_index(self) -> int | None:
        time_position = self.time()
        frame_position = time_position / self._frame_time
        self._last_requested_index = int(frame_position) + self._start_frame_index
        if self.has_frame(self._last_requested_index):
            return self._last_requested_index
        return self.last_index_before(self._last_requested_index)

    @property
    def last_written_index(self) -> int:
        return self._last_written_index

    @property
    def last_requested_index(self) -> int:
        """
        The last requested real frame index (matching to the real timeline)
        :return: int
        """
        return self._last_requested_index

    @property
    def last_returned_index(self) -> int | None:
        """
        The last returned frame index (prepared in the timeline), None if there's no prepared frame
        :return: int | None
        """
        return self._last_returned_index
