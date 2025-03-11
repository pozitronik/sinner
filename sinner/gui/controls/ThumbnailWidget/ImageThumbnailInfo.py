from dataclasses import dataclass
import os
from PIL import Image

from sinner.gui.controls.ThumbnailWidget.BaseThumbnailInfo import BaseThumbnailInfo


@dataclass
class ImageThumbnailInfo(BaseThumbnailInfo):

    @classmethod
    def from_path(cls, path: str):
        """Создает объект ThumbnailInfo из пути к файлу"""

        filename = os.path.basename(path)
        stat_info = os.stat(path)

        # Получаем размер изображения
        with Image.open(path) as img:
            pixel_count = img.size[0] * img.size[1]

        return cls(
            path=path,
            filename=filename,
            mod_date=stat_info.st_mtime,
            file_size=stat_info.st_size,
            pixel_count=pixel_count
        )
