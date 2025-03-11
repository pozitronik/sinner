from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseThumbnailInfo(ABC):
    """Информация о файле миниатюры"""
    path: str
    filename: str
    mod_date: float
    file_size: int
    pixel_count: int

    @classmethod
    @abstractmethod
    def from_path(cls, path: str):
        pass
