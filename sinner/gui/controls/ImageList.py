from tkinter import Frame, Canvas, Scrollbar, Label, Event, TOP, NW, HORIZONTAL, X, BOTTOM
from typing import List, Optional, Tuple

from customtkinter import CTk

from sinner.gui.controls.FrameThumbnail import FrameThumbnail


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
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        self.canvas.create_window((0, 0), window=self.image_frame, anchor=NW, tags="image_frame")
        self.image_frame.bind("<Configure>", self.on_frame_configure)

        self.show(thumbnails)

    def show(self, thumbnails: Optional[List[FrameThumbnail]] = None) -> None:
        if thumbnails is not None:
            if not self.canvas.winfo_manager():
                self.canvas.pack(side=TOP, fill=X, expand=False)
                self.scrollbar.pack(side=BOTTOM, fill=X)

            for label in list(self.image_frame.children.values()):
                label.destroy()

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
