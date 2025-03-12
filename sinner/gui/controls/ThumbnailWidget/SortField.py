from enum import Enum


class SortField(Enum):
    PATH = "Path"
    NAME = "Filename"
    DATE = "Change date"
    SIZE = "File size"
    PIXELS = "Area"
