from tkinter import Canvas

import cv2
from PIL import ImageTk, Image
from PIL.ImageTk import PhotoImage

from sinner.gui.controls.FrameThumbnail import FrameThumbnail
from sinner.typing import Frame


class PreviewCanvas(Canvas):
    photo: PhotoImage | None = None

    @property
    def photo_image(self) -> PhotoImage | None:
        return self.photo

    @photo_image.setter
    def photo_image(self, image: PhotoImage | None) -> None:
        try:  # todo
            self.create_image(self.winfo_width() // 2, self.winfo_height() // 2, image=image)
            self.photo = image
        except Exception as e:
            pass

    def show_frame(self, frame: Frame | None = None) -> None:
        if frame is None:
            self.photo_image = None
        else:
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            image = FrameThumbnail.resize_image(image, (self.winfo_width(), self.winfo_height()))
            self.photo_image = ImageTk.PhotoImage(image)
