from argparse import Namespace
from typing import Callable, Tuple, Optional

import cv2
from PIL import Image

from sinner.gui.controls.ThumbnailWidget.BaseThumbnailInfo import BaseThumbnailInfo
from sinner.gui.controls.ThumbnailWidget.BaseThumbnailWidget import BaseThumbnailWidget
from sinner.gui.controls.ThumbnailWidget.VideoThumbnailInfo import VideoThumbnailInfo
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.helpers.FrameHelper import resize_proportionally
from sinner.typing import Frame
from sinner.utilities import is_video, is_image, get_file_name


class TargetsThumbnailWidget(BaseThumbnailWidget):
    ThumbnailInfoHandler: BaseThumbnailInfo = VideoThumbnailInfo

    def __init__(self, master, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.frame_position: float = kwargs.pop('frame_position', 0.5)  # Position in video (0.0 to 1.0)
        self.parameters: Namespace = kwargs.pop("parameters", Namespace())
        super().__init__(master, **kwargs)

    def add_thumbnail(self, source_path: str, caption: str | bool = True, click_callback: Callable[[str], None] | None = None) -> None:
        """
        Adds an image thumbnail to the widget
        :param source_path: source file path
        :param caption: the thumbnail caption, True to use the file name video format, False to ignore caption
        :param click_callback: on thumbnail click callback
        """
        super().add_thumbnail(source_path, caption, click_callback)

    def _prepare_thumbnail_data(self, source_path: str, caption: str | bool, click_callback: Callable[[str], None] | None) -> Optional[Tuple[Image.Image, str, str | bool, Callable[[str], None] | None]]:
        """
        Prepare thumbnail data in background thread
        """
        thumbnail = self.get_cached_thumbnail(source_path)
        if thumbnail:
            caption = thumbnail.info.get("caption", caption)
        else:
            if is_video(source_path):
                frame, caption = self.get_frame(source_path)
                thumbnail = Image.fromarray(cv2.cvtColor(resize_proportionally(frame, (self.thumbnail_size, self.thumbnail_size)), cv2.COLOR_BGR2RGB))
            elif is_image(source_path):
                thumbnail = Image.open(source_path)
                caption = f"{get_file_name(source_path)} [{thumbnail.size[0]}x{thumbnail.size[1]}]"
                thumbnail.thumbnail((self.thumbnail_size, self.thumbnail_size))
            else:
                return None
            self.set_cached_thumbnail(source_path, thumbnail, caption)
        return thumbnail, source_path, caption, click_callback

    def get_frame(self, video_path: str) -> Tuple[Frame, str]:
        handler = VideoHandler(video_path, self.parameters)
        fc = int(handler.fc * self.frame_position)
        caption = f"{get_file_name(video_path)} [{handler.resolution[0]}x{handler.resolution[1]}]"
        return handler.extract_frame(fc).frame, caption
