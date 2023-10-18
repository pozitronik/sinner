import cv2
from cv2 import VideoCapture

from sinner.typing import Frame


class VideoCamera(VideoCapture):
    _video: str
    _last_frame_render_time: float
    _source_fps: float
    _width: int
    _height: int
    _frame: Frame
    _position: int
    _position_delta: int

    def __init__(self, video: str, last_frame_render_time: float, width: int, height: int):
        super().__init__()
        self._position = 0
        self._video = video
        self._last_frame_render_time = last_frame_render_time
        self._width = width
        self._height = height
        capture = self.open()
        self._source_fps = capture.get(cv2.CAP_PROP_FPS)
        capture.release()

    def open(self) -> VideoCapture:  # type: ignore[override]
        cap = cv2.VideoCapture(self._video)
        if not cap.isOpened():
            raise Exception("Error opening frame file")
        return cap

    def extract_frame(self, frame_number: int) -> Frame:
        capture = self.open()
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)  # zero-based frames
        ret, frame = capture.read()
        capture.release()
        if not ret:
            raise Exception(f"Error reading frame {frame_number}")
        return frame

    def read(self, image: cv2.typing.MatLike | None = None) -> tuple[bool, Frame]:  # type: ignore[name-defined, override]
        self._frame = self.extract_frame(self._position)
        if self._last_frame_render_time == 0:
            self._position += 1
        else:
            self._position += int(self._source_fps * self._last_frame_render_time)
        self._frame = cv2.resize(self._frame, (self._width, self._height))
        return True, self._frame
