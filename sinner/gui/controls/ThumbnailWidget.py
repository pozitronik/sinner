import tkinter as tk
from PIL import Image, ImageTk


class ThumbnailWidget(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.thumbnails = []
        self.thumbnail_width = 100
        self.thumbnail_height = 100
        self.columns = 4
        self.visible_rows = 3
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.grid_rowconfigure(0, weight=1)
        self.canvas.grid_columnconfigure(0, weight=1)
        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.hsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.hsb.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(xscrollcommand=self.hsb.set)

        self.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

    def add_thumbnail(self, image_path):
        if image_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            img = Image.open(image_path)
            img.thumbnail((self.thumbnail_width, self.thumbnail_height))
            photo = ImageTk.PhotoImage(img)

            thumbnail_label = tk.Label(self.frame, image=photo)
            thumbnail_label.image = photo
            thumbnail_label.grid()

            self.thumbnails.append(thumbnail_label)
            self.update_layout()

    def update_layout(self):
        total_width = self.winfo_width()
        self.columns = max(1, total_width // (self.thumbnail_width + 10))  # Adjust the column count based on available width
        for i, thumbnail in enumerate(self.thumbnails):
            row = i // self.columns
            col = i % self.columns
            thumbnail.grid(row=row, column=col)

    def on_canvas_resize(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.update_layout()

    def clear_thumbnails(self):
        for thumbnail in self.thumbnails:
            thumbnail.grid_forget()
        self.thumbnails = []
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))