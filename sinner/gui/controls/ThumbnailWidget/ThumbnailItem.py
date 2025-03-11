from dataclasses import dataclass
from tkinter import Label

from sinner.gui.controls.ThumbnailWidget.ThumbnailInfo import ThumbnailInfo


@dataclass
class ThumbnailItem:
    """Элемент миниатюры в виджете"""
    thumbnail_label: Label
    caption_label: Label
    info: ThumbnailInfo
