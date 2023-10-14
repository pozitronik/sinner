from tkinter import Frame, Canvas, Scrollbar, Label, Event, TOP, NW, HORIZONTAL, X, BOTTOM
from typing import List, Optional, Callable, Tuple, Any

import cv2
from PIL import ImageTk, Image
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

    def photo(self, size: tuple[int, int] = (-1, -1)) -> ImageTk.PhotoImage:
        image: Image = Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
        if size[0] < 0 or size[1] < 0:
            size = image.width // 10, image.height // 10
        image = self.resize_image(image, size)
        return ImageTk.PhotoImage(image)

    @staticmethod
    def resize_image(image: Image, size: tuple[int, int]) -> Image:
        aspect_ratio = image.size[0] / image.size[1]
        new_width = size[0]
        new_height = int(size[0] / aspect_ratio)
        if new_height > size[1]:
            new_height = size[1]
            new_width = int(size[1] * aspect_ratio)
        resized_image = image.resize((new_width, new_height)) if new_width > 0 and new_height > 0 else image
        return resized_image


class ImageList(Frame):
    width: int
    height: int

    def __init__(self, parent: CTk, size: Tuple[int, int] = (-1, -1), thumbnails: Optional[List[FrameThumbnail]] = None):
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

        self.show(thumbnails)

    def show(self, thumbnails: Optional[List[FrameThumbnail]] = None) -> None:
        if thumbnails is not None:
            if not self.canvas.winfo_manager():
                self.canvas.pack(side=TOP, fill=X, expand=False)
                self.scrollbar.pack(side=BOTTOM, fill=X)

            photo = None
            for i, thumbnail in enumerate(thumbnails):
                photo = thumbnail.photo((self.width, self.height))
                image_label = Label(self.image_frame, text=thumbnail.caption, image=photo, compound=TOP)
                image_label.image = photo  # type: ignore[attr-defined]
                image_label.grid(row=0, column=i, padx=10)
                image_label.bind("<Button-1>", lambda event, t=thumbnail, index=i: thumbnail.onclick(thumbnail.position, index))  # type: ignore[misc]
            if photo is not None:
                self.config(height=photo.height())
                self.canvas.config(height=photo.height() + 20)

    def on_frame_configure(self, event: Event) -> None:  # type: ignore[type-arg] # IDK how to fix that :(
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
