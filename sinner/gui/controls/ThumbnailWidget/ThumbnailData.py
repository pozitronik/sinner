import os
from dataclasses import dataclass, field
from typing import Callable, Optional
from PIL import Image

from sinner.utilities import get_file_name


@dataclass
class ThumbnailData:
    """
    Данные для создания миниатюры
    """
    thumbnail: Image.Image  # Обработанное изображение миниатюры
    path: str  # Путь к исходному файлу
    caption: Optional[str]  # Подпись под миниатюрой
    pixel_count: int  # Количество пикселей (WxH) в исходном изображении
    mod_date: float = field(init=False)  # Время изменения исходного файла
    file_size: int = field(init=False)  # Размер исходного файла
    filename: str = field(init=False)  # Имя исходного файла
    click_callback: Optional[Callable[[str], None]] = None  # Опциональный обработчик клика

    def __post_init__(self) -> None:
        """Выполняется после инициализации объекта для заполнения производных полей"""
        self.filename = get_file_name(self.path)
        stat_info = os.stat(self.path)
        self.mod_date = stat_info.st_mtime
        self.file_size = stat_info.st_size
