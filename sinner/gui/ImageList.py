import tkinter as tk
from typing import List, Optional, Literal, Callable

from PIL import ImageTk, Image
from PIL.Image import Resampling

from sinner.typing import Frame


class FrameThumbnail:
    frame: Frame
    caption: str = ''
    position: int
    onclick: Callable[['FrameThumbnail', int], None] | None = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def photo(self, size: tuple[int, int] = (200, 200), resample: Resampling = Resampling.BICUBIC, reducing_gap: float = 2.0) -> ImageTk.PhotoImage:
        image = Image.fromarray(self.frame)
        image.thumbnail(size, resample, reducing_gap)
        return ImageTk.PhotoImage(image)

    def handle_click(self, index: int) -> None:
        if self.onclick:
            self.onclick(self, index)


class ImageList(tk.Frame):
    def __init__(self, parent: tk.Widget, thumbnails: Optional[List[FrameThumbnail]] = None):
        tk.Frame.__init__(self, parent)
        self.canvas: tk.Canvas = tk.Canvas(self, width=400, height=200)
        self.scrollbar: tk.Scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.image_frame: tk.Frame = tk.Frame(self.canvas)
        self.caption_frame: tk.Frame = tk.Frame(self.canvas)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="top", fill="both", expand=True)
        self.scrollbar.pack(side="bottom", fill="x")
        self.canvas.create_window((0, 0), window=self.image_frame, anchor="nw", tags="image_frame")
        self.canvas.create_window((0, 0), window=self.caption_frame, anchor="nw", tags="caption_frame")
        self.image_frame.bind("<Configure>", self.on_frame_configure)
        self.image_widgets: List[tk.Label] = []
        self.caption_labels: List[tk.Label] = []

        self.show(thumbnails)

    def show(self, thumbnails: Optional[List[FrameThumbnail]] = None):
        if thumbnails is not None:
            for i, thumbnail in enumerate(thumbnails):
                photo = thumbnail.photo()
                image_label = tk.Label(self.image_frame, image=photo)
                image_label.image = photo
                image_label.grid(row=0, column=i, padx=10)
                image_label.bind("<Button-1>", lambda event, index=i: thumbnail.handle_click(index))
                self.image_widgets.append(image_label)

                caption_label = tk.Label(self.caption_frame, text=thumbnail.caption)
                caption_label.grid(row=0, column=i, padx=10)
                self.caption_labels.append(caption_label)

    def on_frame_configure(self, event: tk.Event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
