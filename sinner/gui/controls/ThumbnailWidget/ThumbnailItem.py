from dataclasses import dataclass
from tkinter import Label

from sinner.gui.controls.ThumbnailWidget.BaseThumbnailInfo import BaseThumbnailInfo


@dataclass
class ThumbnailItem:
    """Элемент миниатюры в виджете"""
    thumbnail_label: Label
    caption_label: Label
    info: BaseThumbnailInfo
