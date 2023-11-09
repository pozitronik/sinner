from tkinter import Canvas, Frame, Misc, NSEW, Scrollbar, NS, EW, Label, N, UNITS, ALL, Event
from typing import List, Tuple

from PIL import Image
from PIL.ImageTk import PhotoImage

from sinner.utilities import get_file_name, is_image


class ThumbnailWidget(Frame):
    thumbnails: List[Tuple[Label, Label]]
    thumbnail_width: int
    thumbnail_height: int
    canvas: Canvas

    def __init__(self, master: Misc = None, **kwargs):
        super().__init__(master, **kwargs)
        self.thumbnails = []
        self.thumbnail_width = 100
        self.thumbnail_height = 100
        self.columns = 4
        self.visible_rows = 3
        self.canvas = Canvas(self)
        self.canvas.grid(row=0, column=0, sticky=NSEW)
        self.canvas.grid_rowconfigure(0, weight=1)
        self.canvas.grid_columnconfigure(0, weight=1)
        self.frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.vsb = Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.vsb.grid(row=0, column=1, sticky=NS)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.hsb = Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.hsb.grid(row=1, column=0, sticky=EW)
        self.canvas.configure(xscrollcommand=self.hsb.set)

        self.grid(row=0, column=0, sticky=NSEW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # Bind the mouse wheel event to scroll the canvas
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def add_thumbnail(self, image_path, click_callback=None, caption=None):
        if is_image(image_path):
            if caption is None:
                caption = get_file_name(image_path)
            img = Image.open(image_path)
            img.thumbnail((self.thumbnail_width, self.thumbnail_height))
            photo = PhotoImage(img)

            thumbnail_label = Label(self.frame, image=photo)
            thumbnail_label.image = photo
            thumbnail_label.grid()

            # Create a label for the caption and set its width to match the thumbnail width
            caption_label = Label(self.frame, text=caption, wraplength=self.thumbnail_width)
            caption_label.grid(sticky=N)

            if click_callback:
                thumbnail_label.bind("<Button-1>", lambda event, path=image_path: click_callback(path))

            self.thumbnails.append((thumbnail_label, caption_label))
            self.update_layout()

    # noinspection PyTypeChecker
    def update_layout(self):
        total_width = self.winfo_width()
        self.columns = max(1, total_width // (self.thumbnail_width + 10))
        for i, (thumbnail, caption) in enumerate(self.thumbnails):
            row = i // self.columns
            col = i % self.columns
            thumbnail.grid(row=row * 2, column=col)
            caption.grid(row=row * 2 + 1, column=col, )

    # noinspection PyUnusedLocal
    def on_canvas_resize(self, event: Event):
        self.canvas.configure(scrollregion=self.canvas.bbox(ALL))
        self.update_layout()

    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), UNITS)

    def clear_thumbnails(self):
        for thumbnail, caption in self.thumbnails:
            thumbnail.grid_forget()
            caption.grid_forget()
        self.thumbnails = []
        self.canvas.configure(scrollregion=self.canvas.bbox(ALL))
