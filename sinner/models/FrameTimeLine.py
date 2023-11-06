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

    _is_started: bool = False
    _last_written_index: int = 0
    _last_read_index: int = 0

    def __init__(self, frame_time: float, start_frame: int, end_frame: int):
        self._frame_time = frame_time
        self._start_frame_index = start_frame
        self._end_frame_index = end_frame
        self._start_frame_time = start_frame * frame_time
        self._is_started = False
        self._frames = {}

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
        frame_index = self.get_frame_index()
        if self._last_read_index > self._end_frame_index:
            raise EOFError()

        return self._frames[frame_index] if frame_index else None

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
        self._last_read_index = int(frame_position) + self._start_frame_index
        if self._last_read_index in self._frames:
            return self._last_read_index
        return self.last_index_before(self._last_read_index)

    @property
    def last_written_index(self) -> int:
        return self._last_written_index

    @property
    def last_read_index(self) -> int:
        return self._last_read_index
