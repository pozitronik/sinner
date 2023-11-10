from tkinter import Canvas, Frame, Misc, NSEW, Scrollbar, NS, EW, Label, N, UNITS, ALL, Event
from typing import List, Tuple, Callable

from PIL import Image
from PIL.ImageTk import PhotoImage

from sinner.utilities import get_file_name, is_image


class ThumbnailWidget(Frame):
    thumbnails: List[Tuple[Label, Label]]
    thumbnail_width: int
    thumbnail_height: int
    _columns: int
    _canvas: Canvas

    def __init__(self, master: Misc, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(master, **kwargs)
        self.thumbnails = []
        self.thumbnail_width = kwargs['thumbnail_width'] if 'thumbnail_width' in kwargs else 200
        self.thumbnail_height = kwargs['thumbnail_height'] if 'thumbnail_height' in kwargs else 200
        self._canvas = Canvas(self)
        self._canvas.grid(row=0, column=0, sticky=NSEW)
        self._canvas.grid_rowconfigure(0, weight=1)
        self._canvas.grid_columnconfigure(0, weight=1)
        self.frame = Frame(self._canvas)
        self._canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.vsb = Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.vsb.grid(row=0, column=1, sticky=NS)
        self._canvas.configure(yscrollcommand=self.vsb.set)

        self.grid(row=0, column=0, sticky=NSEW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._canvas.bind("<Configure>", self.on_canvas_resize)
        self._canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def add_thumbnail(self, image_path: str, caption: str | bool = True, click_callback: Callable[[str], None] | None = None) -> None:
        """
        Adds an image thumbnail to the widget
        :param image_path: image file path
        :param caption: the thumbnail caption, True to use the file name, False to ignore caption
        :param click_callback: on thumbnail click callback
        """
        if is_image(image_path):
            img = Image.open(image_path)
            img.thumbnail((self.thumbnail_width, self.thumbnail_height))
            photo = PhotoImage(img)

            thumbnail_label = Label(self.frame, image=photo)
            thumbnail_label.image = photo  # type: ignore[attr-defined]
            thumbnail_label.grid()

            # Create a label for the caption and set its width to match the thumbnail width
            caption_label = Label(self.frame, wraplength=self.thumbnail_width)
            if caption is not False:
                if caption is True:
                    caption = get_file_name(image_path)
                caption_label.configure(text=caption)
            caption_label.grid(sticky=N)

            if click_callback:
                thumbnail_label.bind("<Button-1>", lambda event, path=image_path: click_callback(path))  # type: ignore[misc]  #/mypy/issues/4226

            self.thumbnails.append((thumbnail_label, caption_label))
            self.update_layout()
            self.update()
            self.master.update()

    # noinspection PyTypeChecker
    def update_layout(self) -> None:
        total_width = self.winfo_width()
        self._columns = max(1, total_width // (self.thumbnail_width + 10))
        for i, (thumbnail, caption) in enumerate(self.thumbnails):
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
        for thumbnail, caption in self.thumbnails:
            thumbnail.grid_forget()
            caption.grid_forget()
        self.thumbnails = []
        self._canvas.configure(scrollregion=self._canvas.bbox(ALL))
