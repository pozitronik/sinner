from tkinter import Canvas
from PIL.ImageTk import PhotoImage


class PreviewCanvas(Canvas):
    photo: PhotoImage | None = None

    @property
    def photo_image(self) -> PhotoImage | None:
        return self.photo

    @property.setter
    def photo_image(self, image: PhotoImage | None) -> None:
        try:  # todo
            self.create_image(self.winfo_width() // 2, self.winfo_height() // 2, image=image)
            self.photo = image
        except Exception as e:
            pass
