from typing import Callable, Optional

from PIL import Image

from sinner.gui.controls.ThumbnailWidget.BaseThumbnailWidget import BaseThumbnailWidget
from sinner.gui.controls.ThumbnailWidget.ThumbnailData import ThumbnailData
from sinner.utilities import is_image, get_file_name


class SourcesThumbnailWidget(BaseThumbnailWidget):

    def add_thumbnail(self, source_path: str, click_callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Adds an image thumbnail to the widget
        :param source_path: image file path
        :param click_callback: on thumbnail click callback
        """
        if is_image(source_path):
            super().add_thumbnail(source_path, click_callback)

    def _prepare_thumbnail_data(self, source_path: str, click_callback: Optional[Callable[[str], None]] = None) -> Optional[ThumbnailData]:
        """
        Prepare thumbnail data in background thread
        """
        thumbnail = self.get_cached_thumbnail(source_path)
        if not thumbnail:
            thumbnail = self.get_thumbnail(Image.open(source_path), self.thumbnail_size)
            self.set_cached_thumbnail(source_path, thumbnail, get_file_name(source_path))
        caption = thumbnail.info.get("caption") or get_file_name(source_path)
        with Image.open(source_path) as img:  # todo: считать размеры один раз при получении превью, сохраняя в метаданных
            pixel_count = img.size[0] * img.size[1]
        return ThumbnailData(
            thumbnail=thumbnail,
            path=source_path,
            caption=caption,
            click_callback=click_callback,
            pixel_count=pixel_count
        )
