import threading
import time

from sinner.models.FrameDirectoryBuffer import FrameDirectoryBuffer
from sinner.models.NumberedFrame import NumberedFrame


class FrameTimeLine:
    _FrameBuffer: FrameDirectoryBuffer
    _timer: float = 0
    _frame_time: float
    _start_frame_index: int
    _end_frame_index: int
    _start_frame_time: float = 0

    _is_started: bool
    _last_added_index: int = 0
    _last_requested_index: int = 0
    _last_returned_index: int | None = None

    def __init__(self, source_name: str, target_name: str, temp_dir: str, frame_time: float = 0, start_frame: int = 0, end_frame: int = 0):
        self.reload(frame_time, start_frame, end_frame)
        self._is_started = False
        self._FrameBuffer = FrameDirectoryBuffer(source_name, target_name, temp_dir, end_frame)

    def reload(self, frame_time: float, start_frame: int, end_frame: int) -> None:
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
            self._last_returned_index = result_frame.index
        # print("Last requested/returned frame:", f"{self._last_requested_index}/{self._last_returned_index}")
        return result_frame

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
