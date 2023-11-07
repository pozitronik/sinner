from typing import Callable, Any

import cv2
from PIL import ImageTk, Image

from sinner.typing import Frame


class FrameThumbnail:
    frame: Frame
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
