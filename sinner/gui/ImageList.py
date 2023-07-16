import tkinter as tk
from typing import List, Optional, Literal, Callable, Tuple

import cv2
from PIL import ImageTk, Image
from PIL.Image import Resampling

from sinner.typing import Frame


class FrameThumbnail:
    frame: Frame
    caption: str = ''
    position: int
    onclick: Callable[[int, int], None] | None = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def photo(self, size: tuple[int, int] = (400, 400), resample: Resampling = Resampling.BICUBIC, reducing_gap: float = 2.0) -> ImageTk.PhotoImage:
        image = Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
        image.thumbnail(size, resample, reducing_gap)
        return ImageTk.PhotoImage(image)


class ImageList(tk.Frame):
    width: int
    height: int

    def __init__(self, parent: tk.Widget, size: Tuple[int, int] = (400, 400), thumbnails: Optional[List[FrameThumbnail]] = None):
        self.width = size[0]
        self.height = size[1]
        tk.Frame.__init__(self, parent)
        self.canvas: tk.Canvas = tk.Canvas(self)
        self.scrollbar: tk.Scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.image_frame: tk.Frame = tk.Frame(self.canvas)
        self.caption_frame: tk.Frame = tk.Frame(self.canvas)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.canvas.create_window((0, 0), window=self.image_frame, anchor="nw", tags="image_frame")
        self.canvas.create_window((0, 0), window=self.caption_frame, anchor="nw", tags="caption_frame")
        self.image_frame.bind("<Configure>", self.on_frame_configure)
        self.image_widgets: List[tk.Label] = []
        self.caption_labels: List[tk.Label] = []

        self.show(thumbnails)

    def show(self, thumbnails: Optional[List[FrameThumbnail]] = None):
        if thumbnails is not None:
            if not self.canvas.winfo_manager():
                self.canvas.pack(side="top", fill="x", expand=True)
                self.scrollbar.pack(side="bottom", fill="x")

            for i, thumbnail in enumerate(thumbnails):
                photo = thumbnail.photo((self.width, self.height))
                self.canvas.configure(height=min(photo.width(), photo.height()))
                image_label = tk.Label(self.image_frame, image=photo)
                image_label.image = photo
                image_label.grid(row=0, column=i, padx=10)
                image_label.bind("<Button-1>", lambda event, index=i: thumbnail.onclick(thumbnail.position, index))
                self.image_widgets.append(image_label)

                caption_label = tk.Label(self.caption_frame, text=thumbnail.caption)
                caption_label.grid(row=0, column=i, padx=10)
                self.caption_labels.append(caption_label)

    def on_frame_configure(self, event: tk.Event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
