import cv2
from cv2 import VideoCapture

from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.typing import Frame


class ImageCamera(VideoCapture):
    _frame: Frame

    def __init__(self, image: str, width: int, height: int):
        super().__init__()
        self._frame = CV2VideoHandler.read_image(image)
        self._frame = cv2.resize(self._frame, (width, height))

    def read(self, image: cv2.typing.MatLike | None = None) -> tuple[bool, Frame]:  # type: ignore[name-defined, override]
        return True, self._frame
