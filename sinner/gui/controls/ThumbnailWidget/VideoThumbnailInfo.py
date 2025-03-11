from dataclasses import dataclass
import os

from sinner.gui.controls.ThumbnailWidget.BaseThumbnailInfo import BaseThumbnailInfo


@dataclass
class VideoThumbnailInfo(BaseThumbnailInfo):

    @classmethod
    def from_path(cls, path: str):
        """Создает объект ThumbnailInfo из пути к файлу"""
        filename = os.path.basename(path)
        stat_info = os.stat(path)

        return cls(
            path=path,
            filename=filename,
            mod_date=stat_info.st_mtime,
            file_size=stat_info.st_size,
            pixel_count=0
        )
