from typing import Tuple, Callable, Optional

from PIL import Image

from sinner.gui.controls.ThumbnailWidget.BaseThumbnailWidget import BaseThumbnailWidget
from sinner.utilities import is_image


class SourcesThumbnailWidget(BaseThumbnailWidget):

    def add_thumbnail(self, source_path: str, caption: str | bool = True, click_callback: Callable[[str], None] | None = None) -> None:
        """
        Adds an image thumbnail to the widget
        :param source_path: image file path
        :param caption: the thumbnail caption, True to use the file name, False to ignore caption
        :param click_callback: on thumbnail click callback
        """
        if is_image(source_path):
            super().add_thumbnail(source_path, caption, click_callback)

    def _prepare_thumbnail_data(self, source_path: str, caption: str | bool, click_callback: Callable[[str], None] | None) -> Optional[Tuple[Image.Image, str, str | bool, Callable[[str], None]| None]]:
        """
        Prepare thumbnail data in background thread
        """
        thumbnail = self.get_cached_thumbnail(source_path)
        if not thumbnail:
            thumbnail = self.get_thumbnail(Image.open(source_path), self.thumbnail_size)
            self.set_cached_thumbnail(source_path, thumbnail)
        return thumbnail, source_path, caption, click_callback
