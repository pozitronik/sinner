from tkinter import Canvas

import cv2
from PIL import Image
from PIL.ImageTk import PhotoImage

from sinner.gui.controls.BasePlayer import BasePlayer
from sinner.typing import Frame
from sinner.utilities import set_frame_size


class PreviewCanvas(Canvas, BasePlayer):
    photo: PhotoImage | None = None

    _last_frame: Frame | None = None  # the last viewed frame

    @property
    def photo_image(self) -> PhotoImage | None:
        return self.photo

    @photo_image.setter
    def photo_image(self, image: PhotoImage | None) -> None:
        try:  # todo add display modes, add handler on empty image
            self.create_image(self.winfo_width() // 2, self.winfo_height() // 2, image=image)
            self.photo = image
        except Exception as e:
            pass

    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True) -> None:
        """
        Draws an image from the frame, with resize if necessary
        :param frame: frame or None to use the last drawn frame. If last frame is used, it can be only resized
        :param resize: True to resize the current canvas size, False to no resize, tuple(w,h) to set WxH size (proportional)
        """
        if frame is None and self._last_frame is not None:
            frame = self._last_frame
        if frame is not None:
            self._last_frame = frame
            if resize is True:  # resize to the current canvas size
                frame = set_frame_size(frame, (self.winfo_width(), self.winfo_height()))
            elif isinstance(resize, tuple):
                frame = set_frame_size(frame, resize)
            elif resize is False:  # resize the canvas to the image size
                self.adjust_size()
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.photo_image = PhotoImage(image)

    def save_to_file(self, filename: str) -> None:
        if self._last_frame is not None:
            Image.fromarray(cv2.cvtColor(self._last_frame, cv2.COLOR_BGR2RGB)).save(filename)

    def adjust_size(self) -> None:
        if self._last_frame is not None:
            self.configure(width=self._last_frame.shape[1], height=self._last_frame.shape[0])
