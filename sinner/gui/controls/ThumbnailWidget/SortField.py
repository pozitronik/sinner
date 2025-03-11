from enum import Enum


class SortField(Enum):
    PATH = "Путь"
    NAME = "Имя"
    DATE = "Дата изменения"
    SIZE = "Размер файла"
    PIXELS = "Количество пикселей"