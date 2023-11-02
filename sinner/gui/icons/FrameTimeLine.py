import threading
import time
from typing import Dict

from sinner.models.NumberedFrame import NumberedFrame


class FrameTimeLine:
    _frames: Dict[int, NumberedFrame] = {}
    _timer: float = 0
    _frame_time: float
    _start_frame_index: int = 0

    _is_started: bool = False
    _last_frame_index: int = 0

    def __init__(self, frame_time: float, start_frame: int = 0):
        self._frame_time = frame_time
        self._start_frame_index = start_frame
        self._is_started = False
        self._frames = {}

    # start the time counter
    def start(self):
        self._timer = time.perf_counter()
        self._is_started = True

    def stop(self):
        self._is_started = False
        self._frames = {}

    # returns time passed from the start
    def time(self) -> float:
        return time.perf_counter() - self._timer

    def add_frame(self, frame: NumberedFrame) -> int:
        with threading.Lock():
            self._frames[frame.number] = frame
        return len(self._frames)

    # return the frame at current time position, or None, if there's no frame
    def get_frame(self) -> NumberedFrame | None:
        if not self._is_started:
            self.start()
        frame_index = self.get_frame_index()
        frame = None
        if frame_index in self._frames:
            frame = self._frames[frame_index]
        else:
            last_index = self.last_index_before(frame_index)
            if last_index is not None:
                frame = self._frames[last_index]
        return frame

    # naive stub
    def last_index_before(self, index: int) -> int | None:
        indices = list(reversed(self._frames.keys()))
        for current_index in indices:
            if current_index <= index:
                return current_index
        return None

    # return the index of a frame, is playing right now
    def get_frame_index(self) -> int:
        time_position = self.time()
        frame_position = time_position / self._frame_time
        self._last_frame_index = int(frame_position) + self._start_frame_index
        return self._last_frame_index

    @property
    def last_frame_index(self) -> int:
        return self._last_frame_index
