from dataclasses import dataclass


@dataclass
class ThumbnailInfo:
    """Информация о файле миниатюры"""
    path: str
    filename: str
    mod_date: float
    file_size: int
    pixel_count: int

    @classmethod
    def from_path(cls, path: str):
        """Создает объект ThumbnailInfo из пути к файлу"""
        import os
        from PIL import Image

        filename = os.path.basename(path)
        stat_info = os.stat(path)

        # Получаем размер изображения
        with Image.open(path) as img:
            width, height = img.size
            pixel_count = width * height

        return cls(
            path=path,
            filename=filename,
            mod_date=stat_info.st_mtime,
            file_size=stat_info.st_size,
            pixel_count=pixel_count
        )