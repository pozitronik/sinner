import threading
import time
from typing import List, Optional, Self

from sinner.models.FrameDirectoryBuffer import FrameDirectoryBuffer
from sinner.models.NumberedFrame import NumberedFrame


class FrameTimeLine:
    _FrameBuffer: FrameDirectoryBuffer
    _timer: float = 0
    _frame_time: float = 0
    _start_frame_index: int = 0
    _end_frame_index: int = 0
    _start_frame_time: float = 0

    _is_started: bool = False
    _last_added_index: int = 0
    _last_requested_index: int = 0
    _last_returned_index: Optional[int] = None
    _temp_dir: str

    def __init__(self, temp_dir: str) -> None:
        self._temp_dir = temp_dir
        self._FrameBuffer = FrameDirectoryBuffer(self._temp_dir)

    def load(self, source_name: str, target_name: str, frame_time: float = 0, start_frame: int = 0, end_frame: int = 0) -> Self:
        """Loads source/target pair to the timeline"""
        self.reload(frame_time, start_frame, end_frame)
        self._FrameBuffer.load(source_name, target_name, end_frame)
        return self

    def reload(self, frame_time: float, start_frame: int, end_frame: int) -> None:
        """Reloads the same source/target pair"""
        self._frame_time = frame_time
        self._start_frame_index = start_frame
        self._end_frame_index = end_frame
        self._start_frame_time = start_frame * frame_time

    def rewind(self, frame_index: int) -> None:
        self._start_frame_index = frame_index
        self._start_frame_time = self._start_frame_index * self._frame_time
        self._FrameBuffer.clean()
        if self._is_started:
            self._timer = time.perf_counter()

    # start the time counter
    def start(self) -> None:
        self._timer = time.perf_counter()
        self._is_started = True

    def stop(self) -> None:
        self._is_started = False
        self._FrameBuffer.clean()

    # returns time passed from the start
    def time(self) -> float:
        if self._is_started:
            return time.perf_counter() - self._timer
        else:
            return 0.0

    def real_time_position(self) -> float:
        """
        Return timeline position in seconds from the beginning of the processing
        :return: float
        """
        return self.time() + self._start_frame_time

    def add_frame(self, frame: NumberedFrame) -> None:
        with threading.Lock():
            self._FrameBuffer.add_frame(frame)
            self._last_added_index = frame.index

    def add_frame_index(self, index: int) -> None:
        with threading.Lock():
            self._FrameBuffer.add_index(index)
            self._last_added_index = index

    # return the frame at current time position, or None, if there's no frame
    def get_frame(self, time_aligned: bool = True) -> NumberedFrame | None:
        if not self._is_started:
            self.start()
        if time_aligned:
            self._last_requested_index = self.get_frame_index()
        else:
            self._last_requested_index = self.last_added_index
        if self._last_requested_index > self._end_frame_index:
            raise EOFError()

        result_frame = self._FrameBuffer.get_frame(self._last_requested_index)
        if result_frame:
            self._last_returned_index = self._last_requested_index  # it is an EXPECTED index, not a real one
        return result_frame

    def get_frame_by_index(self, index: int) -> NumberedFrame | None:
        return self._FrameBuffer.get_frame(index, False)

    def has_index(self, index: int) -> bool:
        return self._FrameBuffer.has_index(index)

    # return the index of a frame, is playing right now if it is in self._frames
    # else return last frame before requested
    def get_frame_index(self) -> int:
        time_position = self.time()
        frame_position = time_position / self._frame_time
        return int(frame_position) + self._start_frame_index

    @property
    def last_added_index(self) -> int:
        return self._last_added_index

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

    @property
    def frame_lag(self) -> int:
        """
        :return: the difference between currently playing frame and the last returned one. Shows the processing lag.
        """
        return self.get_frame_index() - (self._last_returned_index or self._start_frame_index)

    @property
    def time_lag(self) -> float:
        """
        :return: the time difference between currently playing frame and the last requested one.
        """
        return self.frame_lag * self._frame_time

    @property
    def display_frame_lag(self) -> int:
        """
        :return: the difference between current frame and the last returned one. Shows the visible lag.
        """
        return (self._last_returned_index or self._start_frame_index) - self._last_added_index

    @property
    def display_time_lag(self) -> float:
        """
        :return: the time difference between current frame and the last returned one.
        """
        return self.display_frame_lag * self._frame_time

    @property
    def current_frame_miss(self) -> int:
        """
        :return: the current *real* gap between requested frame and returned one
        """
        return self._FrameBuffer.miss

    @property
    def processed_frames(self) -> List[int]:
        """
        :return: the list of already processed frames
        """
        return self._FrameBuffer.get_indices()
