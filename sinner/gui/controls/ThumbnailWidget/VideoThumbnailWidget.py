from argparse import Namespace
from typing import Callable, Tuple

import cv2
from PIL import Image

from sinner.gui.controls.ThumbnailWidget.BaseThumbnailWidget import BaseThumbnailWidget
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.helpers.FrameHelper import resize_proportionally
from sinner.typing import Frame
from sinner.utilities import is_video


class VideoThumbnailWidget(BaseThumbnailWidget):

    def __init__(self, master, **kwargs):  # type: ignore[no-untyped-def]
        self.frame_position: float = kwargs.pop('frame_position', 0.5)  # Position in video (0.0 to 1.0)
        super().__init__(master, **kwargs)

    def add_thumbnail(self, source_path: str, caption: str | bool = True, click_callback: Callable[[str], None] | None = None) -> None:
        """
        Adds an image thumbnail to the widget
        :param source_path: video file path
        :param caption: the thumbnail caption, True to use the file name, False to ignore caption
        :param click_callback: on thumbnail click callback
        """
        if is_video(source_path):
            super().add_thumbnail(source_path, caption, click_callback)

    def _prepare_thumbnail_data(self, video_path: str, caption: str | bool, click_callback: Callable[[str], None] | None) -> Tuple[Image.Image, str, str | bool, Callable[[str], None] | None]:
        """
        Prepare thumbnail data in background thread
        """
        img = self.get_cached_thumbnail(video_path)
        if not img:
            img = Image.fromarray(cv2.cvtColor(resize_proportionally(self.get_frame(video_path), (self.thumbnail_size, self.thumbnail_size)), cv2.COLOR_BGR2RGB))
            self.set_cached_thumbnail(video_path, img)
        return img, video_path, caption, click_callback

    def get_frame(self, video_path: str) -> Frame:
        handler = VideoHandler(video_path, Namespace())
        fc = int(handler.fc * self.frame_position)
        return handler.extract_frame(fc).frame
