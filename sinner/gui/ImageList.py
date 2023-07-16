from tkinter import Frame, Canvas, Scrollbar, Label, Event, TOP, NW, HORIZONTAL
from typing import List, Optional, Callable, Tuple, Any

import cv2
from PIL import ImageTk, Image
from PIL.Image import Resampling
from customtkinter import CTk

from sinner import typing


class FrameThumbnail:
    frame: typing.Frame
    caption: str = ''
    position: int
    onclick: Callable[[int, int], None]

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def photo(self, size: tuple[int, int] = (400, 400), resample: Resampling = Resampling.BICUBIC, reducing_gap: float = 2.0) -> ImageTk.PhotoImage:
        image = Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
        image.thumbnail(size, resample, reducing_gap)
        return ImageTk.PhotoImage(image)


class ImageList(Frame):
    width: int
    height: int

    def __init__(self, parent: CTk, size: Tuple[int, int] = (400, 400), thumbnails: Optional[List[FrameThumbnail]] = None):
        self.width = size[0]
        self.height = size[1]
        Frame.__init__(self, parent)
        self.canvas: Canvas = Canvas(self)
        self.scrollbar: Scrollbar = Scrollbar(self, orient=HORIZONTAL, command=self.canvas.xview)
        self.image_frame: Frame = Frame(self.canvas)
        self.caption_frame: Frame = Frame(self.canvas)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.canvas.create_window((0, 0), window=self.image_frame, anchor=NW, tags="image_frame")
        self.canvas.create_window((0, 0), window=self.caption_frame, anchor=NW, tags="caption_frame")
        self.image_frame.bind("<Configure>", self.on_frame_configure)
        self.image_widgets: List[Label] = []
        self.caption_labels: List[Label] = []

        self.show(thumbnails)

    def show(self, thumbnails: Optional[List[FrameThumbnail]] = None) -> None:
        if thumbnails is not None:
            if not self.canvas.winfo_manager():
                self.canvas.pack(side="top", fill="x", expand=True)
                self.scrollbar.pack(side="bottom", fill="x")

            for i, thumbnail in enumerate(thumbnails):
                photo = thumbnail.photo((self.width, self.height))
                # self.canvas.configure(height=min(photo.width(), photo.height()))
                image_label = Label(self.image_frame, text=thumbnail.caption, image=photo, compound=TOP)
                image_label.image = photo  # type: ignore[attr-defined]
                image_label.grid(row=0, column=i, padx=10)
                image_label.bind("<Button-1>", lambda event, t=thumbnail, index=i: thumbnail.onclick(thumbnail.position, index))  # type: ignore[misc]

    def on_frame_configure(self, event: Event) -> None:  # type: ignore[type-arg] # idk how to fix that :(
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
