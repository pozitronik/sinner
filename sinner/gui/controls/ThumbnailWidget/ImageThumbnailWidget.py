from tkinter import Label, N
from typing import  Tuple, Callable

from PIL import Image
from PIL.ImageTk import PhotoImage

from sinner.gui.controls.ThumbnailWidget.BaseThumbnailWidget import BaseThumbnailWidget
from sinner.utilities import get_file_name, is_image


class ImageThumbnailWidget(BaseThumbnailWidget):

    def add_thumbnail(self, source_path: str, caption: str | bool = True, click_callback: Callable[[str], None] | None = None) -> None:
        """
        Adds an image thumbnail to the widget
        :param source_path: image file path
        :param caption: the thumbnail caption, True to use the file name, False to ignore caption
        :param click_callback: on thumbnail click callback
        """
        if is_image(source_path):
            # Подготавливаем параметры для обработки
            params = (source_path, caption, click_callback)

            # Создаём задачу для обработки изображения
            future = self._executor.submit(self._prepare_thumbnail_data, *params)

            with self._processing_lock:
                self._pending_futures.append(future)
                if not self._is_processing:
                    self._is_processing = True
                    self.after(100, self._process_pending)

    def _prepare_thumbnail_data(self, image_path: str, caption: str | bool, click_callback: Callable[[str], None] | None) -> Tuple[Image.Image, str, str | bool, Callable[[str], None] | None]:
        """
        Prepare thumbnail data in background thread
        """
        img = self.get_cached_thumbnail(image_path)
        if not img:
            img = self.get_thumbnail(Image.open(image_path), self.thumbnail_size)
            self.set_cached_thumbnail(image_path, img)
        return img, image_path, caption, click_callback

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
                img, image_path, caption, click_callback = future.result()
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
