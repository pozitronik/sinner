import hashlib
import os
import tempfile
from tkinter import Canvas, Frame, Misc, NSEW, Scrollbar, Label, N, UNITS, ALL, Event, NW, LEFT, Y, BOTH
from typing import List, Tuple, Callable

from PIL import Image
from PIL.ImageTk import PhotoImage

from sinner.utilities import get_file_name, is_image


class ThumbnailWidget(Frame):
    thumbnails: List[Tuple[Label, Label, str]]
    thumbnail_size: int
    temp_dir: str
    _columns: int
    _canvas: Canvas

    def __init__(self, master: Misc, **kwargs):  # type: ignore[no-untyped-def]
        # custom parameters
        self.thumbnail_size = kwargs.pop('thumbnail_size', 200)
        self.temp_dir = os.path.abspath(os.path.join(os.path.normpath(kwargs.pop('temp_dir', tempfile.gettempdir())), 'thumbnails'))
        os.makedirs(self.temp_dir, exist_ok=True)
        super().__init__(master, **kwargs)
        self.thumbnails = []
        self._canvas = Canvas(self)
        self._canvas.pack(side=LEFT, expand=True, fill=BOTH)
        # self._canvas.grid(row=0, column=0, sticky=NSEW)
        # self._canvas.grid_rowconfigure(0, weight=1)
        # self._canvas.grid_columnconfigure(0, weight=1)
        self.frame = Frame(self._canvas)
        self._canvas.create_window((0, 0), window=self.frame, anchor=NW)

        self.vsb = Scrollbar(self, orient="vertical", command=self._canvas.yview)
        # self.vsb.grid(row=0, column=1, sticky=NS)
        self.vsb.pack(side=LEFT, fill=Y)
        self._canvas.configure(yscrollcommand=self.vsb.set)

        self.grid(row=0, column=0, sticky=NSEW)
        # self.grid_rowconfigure(0, weight=1)
        # self.grid_columnconfigure(0, weight=1)
        self._canvas.bind("<Configure>", self.on_canvas_resize)
        self._canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def get_cached_thumbnail(self, image_path: str) -> Image.Image | None:
        thumb_name = hashlib.md5(f"{image_path}{self.thumbnail_size}".encode()).hexdigest() + '.png'
        thumb_path = os.path.join(self.temp_dir, thumb_name)
        if os.path.exists(thumb_path):
            return Image.open(thumb_path)
        return None

    def set_cached_thumbnail(self, image_path: str, img: Image.Image) -> None:
        thumb_name = hashlib.md5(f"{image_path}{self.thumbnail_size}".encode()).hexdigest() + '.png'
        thumb_path = os.path.join(self.temp_dir, thumb_name)
        img.save(thumb_path, 'PNG')

    @staticmethod
    def get_thumbnail(image: Image, size: int) -> Image:
        """
        Crops an image to a square with the given size, centering the crop around the middle of the image.
        :param image: A PIL Image instance.
        :param size: The desired size of each side of the square.
        :return: A square PIL Image instance.
        """
        width, height = image.size

        # Determine the size of the square and the coordinates to crop the image.
        min_side = min(width, height)
        left = (width - min_side) // 2
        top = (height - min_side) // 2
        right = (width + min_side) // 2
        bottom = (height + min_side) // 2

        # Crop and resize the image to the specified size.
        image = image.crop((left, top, right, bottom))
        image.thumbnail((size, size))
        return image

    def add_thumbnail(self, image_path: str, caption: str | bool = True, click_callback: Callable[[str], None] | None = None) -> None:
        """
        Adds an image thumbnail to the widget
        :param image_path: image file path
        :param caption: the thumbnail caption, True to use the file name, False to ignore caption
        :param click_callback: on thumbnail click callback
        """
        if is_image(image_path):
            img = self.get_cached_thumbnail(image_path)
            if not img:
                img = self.get_thumbnail(Image.open(image_path), self.thumbnail_size)
                self.set_cached_thumbnail(image_path, img)
            photo = PhotoImage(img)

            thumbnail_label = Label(self.frame, image=photo)
            thumbnail_label.image = photo  # type: ignore[attr-defined]
            thumbnail_label.grid()

            # Create a label for the caption and set its width to match the thumbnail width
            caption_label = Label(self.frame, wraplength=self.thumbnail_size)
            if caption is not False:
                if caption is True:
                    caption = get_file_name(image_path)
                caption_label.configure(text=caption)
            caption_label.grid(sticky=N)

            if click_callback:
                thumbnail_label.bind("<Button-1>", lambda event, path=image_path: click_callback(path))  # type: ignore[misc]  #/mypy/issues/4226
                caption_label.bind("<Button-1>", lambda event, path=image_path: click_callback(path))  # type: ignore[misc]  #/mypy/issues/4226

            self.thumbnails.append((thumbnail_label, caption_label, image_path))
            self.sort_thumbnails()
            self.update()
            self.master.update()

    def sort_thumbnails(self, asc: bool = True) -> None:
        # Sort the thumbnails list by the image path
        if asc:
            self.thumbnails.sort(key=lambda x: x[2])  # Assuming x[1] is the image path
        else:
            self.thumbnails.sort(key=lambda x: x[2], reverse=True)

        # Update the GUI to reflect the new order
        self.update_layout()

    # noinspection PyTypeChecker
    def update_layout(self) -> None:
        if 0 == len(self.thumbnails):
            return
        total_width = self.winfo_width()
        self._columns = max(1, total_width // (self.thumbnail_size + 10))
        for i, (thumbnail, caption, path) in enumerate(self.thumbnails):
            row = i // self._columns
            col = i % self._columns
            thumbnail.grid(row=row * 2, column=col)
            caption.grid(row=row * 2 + 1, column=col, )
        self._canvas.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox(ALL))

    # noinspection PyUnusedLocal
    def on_canvas_resize(self, event: Event) -> None:  # type: ignore[type-arg]
        self._canvas.configure(scrollregion=self._canvas.bbox(ALL))
        self.update_layout()

    def on_mouse_wheel(self, event: Event) -> None:  # type: ignore[type-arg]
        # Get the bounding box of all items on the canvas
        bbox = self._canvas.bbox(ALL)

        # Compare the canvas content size to the visible area
        canvas_width = self._canvas.winfo_width()
        canvas_height = self._canvas.winfo_height()

        content_width = bbox[2] - bbox[0]
        content_height = bbox[3] - bbox[1]

        # If content fits within the visible area, do not scroll
        if content_width <= canvas_width and content_height <= canvas_height:
            return
        self._canvas.yview_scroll(-1 * (event.delta // 120), UNITS)

    def clear_thumbnails(self) -> None:
        for thumbnail, caption, path in self.thumbnails:
            thumbnail.grid_forget()
            caption.grid_forget()
        self.thumbnails = []
        self._canvas.configure(scrollregion=self._canvas.bbox(ALL))
