import hashlib
import os
import tempfile
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from multiprocessing import cpu_count
from tkinter import Canvas, Frame, Misc, NSEW, Scrollbar, Label, N, UNITS, ALL, Event, NW, LEFT, Y, BOTH
from typing import List, Tuple, Callable, Optional

from PIL import Image
from PIL.ImageTk import PhotoImage
from PIL.PngImagePlugin import PngInfo

from sinner.utilities import get_file_name


class BaseThumbnailWidget(Frame, ABC):
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

        self._executor = ThreadPoolExecutor(max_workers=cpu_count())
        self._pending_futures: List[Future[Optional[Tuple[Image.Image, str, str | bool, Callable[[str], None] | None]]]] = []
        self._processing_lock = threading.Lock()
        self._is_processing = False

        self._canvas = Canvas(self)
        self._canvas.pack(side=LEFT, expand=True, fill=BOTH)
        self.frame = Frame(self._canvas)
        self._canvas.create_window((0, 0), window=self.frame, anchor=NW)

        self.vsb = Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.vsb.pack(side=LEFT, fill=Y)
        self._canvas.configure(yscrollcommand=self.vsb.set)

        self.grid(row=0, column=0, sticky=NSEW)
        self._canvas.bind("<Configure>", self.on_canvas_resize)
        self.bind_mousewheel()

    def get_cached_thumbnail(self, source_path: str) -> Image.Image | None:
        thumb_name = hashlib.md5(f"{source_path}{self.thumbnail_size}".encode()).hexdigest() + '.png'
        thumb_path = os.path.join(self.temp_dir, thumb_name)
        if os.path.exists(thumb_path):
            return Image.open(thumb_path)
        return None

    def set_cached_thumbnail(self, source_path: str, img: Image.Image, caption: str | None = None) -> None:
        thumb_name = hashlib.md5(f"{source_path}{self.thumbnail_size}".encode()).hexdigest() + '.png'
        thumb_path = os.path.join(self.temp_dir, thumb_name)
        metadata_dict = PngInfo()
        if caption:
            metadata_dict.add_text("caption", caption)
        img.save(thumb_path, 'PNG', pnginfo=metadata_dict)

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

    @abstractmethod
    def add_thumbnail(self, source_path: str, caption: str | bool = True, click_callback: Callable[[str], None] | None = None) -> None:
        """
        Adds an image thumbnail to the widget
        :param source_path: source file path
        :param caption: the thumbnail caption, True to use the file name, False to ignore caption
        :param click_callback: on thumbnail click callback
        """
        # Подготавливаем параметры для обработки
        params = (source_path, caption, click_callback)

        # Создаём задачу для обработки изображения
        future = self._executor.submit(self._prepare_thumbnail_data, *params)

        with self._processing_lock:
            self._pending_futures.append(future)
            if not self._is_processing:
                self._is_processing = True
                self.after(100, self._process_pending)

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

    def bind_mousewheel(self) -> None:
        def _bind_wheel(event: Event) -> None:  # type: ignore[type-arg]
            self._canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        def _unbind_wheel(event: Event) -> None:  # type: ignore[type-arg]
            self._canvas.unbind_all("<MouseWheel>")

        self._canvas.bind("<Enter>", _bind_wheel)
        self._canvas.bind("<Leave>", _unbind_wheel)

    def on_mouse_wheel(self, event: Event) -> None:  # type: ignore[type-arg]
        # Получаем координаты курсора относительно канваса
        canvas_x = self._canvas.winfo_rootx()
        canvas_y = self._canvas.winfo_rooty()
        canvas_width = self._canvas.winfo_width()
        canvas_height = self._canvas.winfo_height()

        # Проверяем, находится ли курсор над канвасом
        if not (canvas_x <= event.x_root <= canvas_x + canvas_width and
                canvas_y <= event.y_root <= canvas_y + canvas_height):
            return

        # Get the bounding box of all items on the canvas
        bbox = self._canvas.bbox(ALL)
        if not bbox:
            return

        # Compare the canvas content size to the visible area
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
        with self._processing_lock:
            self._pending_futures.clear()
            self._is_processing = False

    @abstractmethod
    def _prepare_thumbnail_data(self, source_path: str, caption: str | bool, click_callback: Callable[[str], None] | None) -> Optional[Tuple[Image.Image, str, str | bool, Callable[[str], None] | None]]:
        """
        Prepare thumbnail data in background thread
        """
        pass

    def _process_pending(self) -> None:
        """
        Process completed thumbnail preparations and update GUI when all are done
        """
        completed = []
        ongoing = []

        # Проверяем завершённые задачи
        with self._processing_lock:
            for future in self._pending_futures:
                if future.done():
                    completed.append(future)
                else:
                    ongoing.append(future)
            self._pending_futures = ongoing

        # Обрабатываем завершённые
        for future in completed:
            try:
                result = future.result()
                if result is None:
                    continue
                img, image_path, caption, click_callback = result
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
                    thumbnail_label.bind("<Button-1>", lambda event, path=image_path: click_callback(path))  # type: ignore[misc]
                    caption_label.bind("<Button-1>", lambda event, path=image_path: click_callback(path))  # type: ignore[misc]

                self.thumbnails.append((thumbnail_label, caption_label, image_path))
            except Exception as e:
                print(f"Error processing thumbnail {image_path}: {e}")

        # Если есть завершённые задачи, обновляем layout
        if completed:
            self.sort_thumbnails()
            self.update()
            self.master.update()

        # Продолжаем обработку, если есть незавершённые задачи
        with self._processing_lock:
            if self._pending_futures:
                self.after(100, self._process_pending)
            else:
                self._is_processing = False
