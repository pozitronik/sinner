import hashlib
import os
import tempfile
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from multiprocessing import cpu_count
from tkinter import Canvas, Frame, Misc, NSEW, Scrollbar, Label, N, UNITS, ALL, Event, NW, LEFT, Y, BOTH, TOP, X, Entry, StringVar
from typing import List, Callable, Optional, Set

from PIL import Image
from PIL.ImageTk import PhotoImage
from PIL.PngImagePlugin import PngInfo

from sinner.gui.controls.ThumbnailWidget.SortControlPanel import SortControlPanel
from sinner.gui.controls.ThumbnailWidget.SortField import SortField
from sinner.gui.controls.ThumbnailWidget.ThumbnailData import ThumbnailData
from sinner.gui.controls.ThumbnailWidget.ThumbnailItem import ThumbnailItem


class BaseThumbnailWidget(Frame, ABC):
    thumbnails: List[ThumbnailItem]
    thumbnail_size: int
    temp_dir: str
    _columns: int
    _canvas: Canvas
    thumbnail_paths: Set[str]  # отдельный словарь для путей для O(1) поиска
    selected_paths: Set[str]  # словарь для путей выбранных файлов
    _highlight_color: str
    _background_color: str
    _current_sort_field: SortField
    _current_sort_ascending: bool
    _sort_control: SortControlPanel
    _thumbnail_click_callback: Optional[Callable[[str], None]] = None
    _filter_text: StringVar
    _filtered_thumbnails: List[ThumbnailItem]

    def __init__(self, master: Misc, **kwargs):  # type: ignore[no-untyped-def]
        # custom parameters
        self.thumbnail_size = kwargs.pop('thumbnail_size', 200)
        self.temp_dir = os.path.abspath(os.path.join(os.path.normpath(kwargs.pop('temp_dir', tempfile.gettempdir())), 'thumbnails'))
        os.makedirs(self.temp_dir, exist_ok=True)
        self._highlight_color = kwargs.pop('highlight_color', '#E3F3FF')  # Светло-голубой цвет фона для выделения
        self._background_color = kwargs.pop('background_color', '#F0F0F0')  # Обычный цвет фона
        self._show_sort_control = kwargs.pop('show_sort_control', True)  # Показывать ли контрол сортировки
        self._thumbnail_click_callback = kwargs.pop('click_callback', None)  # Обработчик выбора миниатюры

        # Параметры фильтрации
        self._filter_text = StringVar()
        self._filter_text.trace_add("write", self._on_filter_changed)

        super().__init__(master, **kwargs)
        self.thumbnails = []
        self._filtered_thumbnails = self.thumbnails.copy()  # Инициализация фильтрованного списка
        self.thumbnail_paths = set()
        self.selected_paths = set()

        # Параметры сортировки по умолчанию
        self._current_sort_field = SortField.NAME
        self._current_sort_ascending = True

        self._executor = ThreadPoolExecutor(max_workers=cpu_count())
        self._pending_futures: List[Future[ThumbnailData]] = []
        self._processing_lock = threading.Lock()
        self._is_processing = False

        # Создаем фрейм для элементов управления
        self.control_frame = Frame(self)
        self.control_frame.pack(side=TOP, fill=X, padx=5, pady=5)

        # Добавляем фильтр поиска
        filter_frame = Frame(self.control_frame)
        filter_frame.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        filter_label = Label(filter_frame, text="Filter:")
        filter_label.pack(side=LEFT, padx=(0, 5))

        self.filter_entry = Entry(filter_frame, textvariable=self._filter_text)
        self.filter_entry.pack(side=LEFT, fill=X, expand=True)

        clear_btn = Label(filter_frame, text="✕", cursor="hand2", padx=5)
        clear_btn.pack(side=LEFT)
        clear_btn.bind("<Button-1>", lambda e: self.clear_filter())

        # Создаем контрол сортировки
        if self._show_sort_control:
            self._sort_control = SortControlPanel(
                self.control_frame,
                on_sort_changed=self._on_sort_changed
            )
            self._sort_control.pack(side=LEFT)

        # Создаем основной фрейм для виджета
        self.content_frame = Frame(self)
        self.content_frame.pack(side=TOP, fill=BOTH, expand=True)

        # Создаем канву и прокрутку
        self._canvas = Canvas(self.content_frame)
        self._canvas.pack(side=LEFT, expand=True, fill=BOTH)
        self.frame = Frame(self._canvas)
        self._canvas.create_window((0, 0), window=self.frame, anchor=NW)

        self.vsb = Scrollbar(self.content_frame, orient="vertical", command=self._canvas.yview)
        self.vsb.pack(side=LEFT, fill=Y)
        self._canvas.configure(yscrollcommand=self.vsb.set)

        self.grid(row=0, column=0, sticky=NSEW)
        self._canvas.bind("<Configure>", self.on_canvas_resize)
        self.bind_mousewheel()

        # Предопределенные функции сортировки
        self._sort_keys = {
            SortField.PATH: lambda x: x.data.path,
            SortField.NAME: lambda x: x.data.filename.lower(),
            SortField.DATE: lambda x: x.data.mod_date,
            SortField.SIZE: lambda x: x.data.file_size,
            SortField.PIXELS: lambda x: x.data.pixel_count
        }

    def destroy(self) -> None:
        """Clean up resources when widget is destroyed"""
        self._executor.shutdown(wait=False)
        super().destroy()

    def _on_sort_changed(self, field: SortField, ascending: bool) -> None:
        """
        Обработчик изменения параметров сортировки из контрола

        :param field: Выбранное поле сортировки
        :param ascending: Порядок сортировки (True - по возрастанию)
        """
        self._current_sort_field = field
        self._current_sort_ascending = ascending
        self.sort_thumbnails(field, ascending)

    def _on_filter_changed(self, *args) -> None:  # type: ignore[no-untyped-def]
        """Обработчик изменения текста фильтра"""
        self._apply_filter()
        self.update_layout()

    def _apply_filter(self) -> None:
        """Применяет текущий фильтр к списку миниатюр"""
        filter_text = self._filter_text.get().lower()

        if not filter_text:
            # Если фильтр пустой, показываем все миниатюры
            self._filtered_thumbnails = self.thumbnails.copy()
        else:
            # Иначе фильтруем по тексту в заголовке
            self._filtered_thumbnails = [
                item for item in self.thumbnails
                if item.data.caption is not None and filter_text in item.data.caption.lower()
            ]

    def clear_filter(self) -> None:
        """Очищает текущий фильтр"""
        self._filter_text.set("")

    @property
    def highlight_color(self) -> str:
        """Возвращает текущий цвет выделения."""
        return self._highlight_color

    @highlight_color.setter
    def highlight_color(self, value: str) -> None:
        """
        Устанавливает цвет выделения и обновляет все выделенные миниатюры.
        :param value: Цвет в формате HEX (#RRGGBB) или имя цвета
        """
        self._highlight_color = value
        self.update_layout(False)  # Обновляем все элементы с новым цветом

    def get_cached_thumbnail(self, source_path: str) -> Image.Image | None:
        thumb_name = hashlib.md5(f"{source_path}{self.thumbnail_size}".encode()).hexdigest() + '.png'
        thumb_path = os.path.join(self.temp_dir, thumb_name)
        if os.path.exists(thumb_path):
            with Image.open(thumb_path) as img:
                return img.copy()
        return None

    def set_cached_thumbnail(self, source_path: str, img: Image.Image, caption: Optional[str] = None, pixel_count: Optional[int] = None) -> None:
        thumb_name = hashlib.md5(f"{source_path}{self.thumbnail_size}".encode()).hexdigest() + '.png'
        thumb_path = os.path.join(self.temp_dir, thumb_name)
        metadata_dict = PngInfo()
        if caption:
            metadata_dict.add_text("caption", caption)
        if pixel_count:
            metadata_dict.add_text("pixel_count", str(pixel_count))
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
    def add_thumbnail(self, source_path: str, click_callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Adds an image thumbnail to the widget
        :param source_path: source file path
        :param click_callback: on thumbnail click callback. None: global callback will be used
        """
        # Подготавливаем параметры для обработки
        params = (source_path, click_callback or self._thumbnail_click_callback)

        # Создаём задачу для обработки изображения
        future = self._executor.submit(self._prepare_thumbnail_data, *params)

        with self._processing_lock:
            self._pending_futures.append(future)
            if not self._is_processing:
                self._is_processing = True
                self.after(100, self._process_pending)

    def select_thumbnail(self, path: str, exclusive: bool = True) -> None:
        """
        Выделяет миниатюру по указанному пути к файлу
        :param path: Путь к файлу миниатюры для выделения
        :param exclusive: Если True, снимает выделение со всех остальных миниатюр
        """
        if exclusive:
            self.clear_selection()

        if path in self.thumbnail_paths:
            self.selected_paths.add(path)
            self.update_layout(False)

    def deselect_thumbnail(self, path: str) -> None:
        """
        Снимает выделение с миниатюры по указанному пути к файлу
        :param path: Путь к файлу миниатюры для снятия выделения
        """
        if path in self.selected_paths:
            self.selected_paths.remove(path)
            self.update_layout(False)

    def toggle_thumbnail_selection(self, path: str) -> None:
        """
        Переключает состояние выделения миниатюры по указанному пути к файлу
        :param path: Путь к файлу миниатюры для переключения состояния
        """
        if path in self.selected_paths:
            self.deselect_thumbnail(path)
        else:
            self.select_thumbnail(path, exclusive=False)

    def clear_selection(self) -> None:
        """
        Снимает выделение со всех выделенных миниатюр
        """
        self.selected_paths.clear()
        self.update_layout(False)

    def get_selected_thumbnails(self) -> List[str]:
        """
        Возвращает пути всех выделенных миниатюр
        :return: Список путей выделенных миниатюр
        """
        return list(self.selected_paths)

    def sort_thumbnails(self, field: SortField = SortField.NAME, asc: bool = True) -> None:
        """
        Сортирует миниатюры по указанному полю
        :param field: Поле для сортировки (из enum SortField)
        :param asc: Направление сортировки (True - по возрастанию, False - по убыванию)
        """
        # Используем текущие параметры сортировки, если не указаны новые
        if field is None:
            field = self._current_sort_field
        else:
            self._current_sort_field = field

        if asc is None:
            asc = self._current_sort_ascending
        else:
            self._current_sort_ascending = asc

        # Обновляем контрол сортировки, если он существует
        if self._show_sort_control:
            self._sort_control.set_sort(field, asc)

        # Получаем функцию сортировки из предопределенного словаря
        key_func = self._sort_keys.get(field, self._sort_keys[SortField.PATH])

        # Сортируем
        self.thumbnails.sort(key=key_func, reverse=not asc)

        # Переприменяем фильтр к отсортированному списку
        self._apply_filter()

        # Обновляем интерфейс
        self.update_layout()

    # noinspection PyTypeChecker
    def update_layout(self, update_grid: bool = True) -> None:
        if 0 == len(self.thumbnails):
            return

        # Скрываем все миниатюры при обновлении сетки
        if update_grid:
            for item in self.thumbnails:
                item.thumbnail_label.grid_remove()
                item.caption_label.grid_remove()

        # Если нет видимых миниатюр после фильтрации
        if 0 == len(self._filtered_thumbnails):
            self._canvas.configure(scrollregion=self._canvas.bbox(ALL))
            return

        total_width = self.winfo_width()
        # Минимальная ширина, если виджет еще не отрисован
        if total_width <= 1:
            total_width = 200
        self._columns = max(1, total_width // (self.thumbnail_size + 10))

        # Показываем только отфильтрованные миниатюры
        for i, item in enumerate(self._filtered_thumbnails):
            if update_grid:
                row = i // self._columns
                col = i % self._columns
                item.thumbnail_label.grid(row=row * 2, column=col)
                item.caption_label.grid(row=row * 2 + 1, column=col)

            # Обновляем состояние выделения для каждой миниатюры
            if item.data.path in self.selected_paths:
                item.caption_label.configure(background=self._highlight_color)
            else:
                item.caption_label.configure(background=self._background_color)

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
        # Получаем координаты курсора относительно канвы
        canvas_x = self._canvas.winfo_rootx()
        canvas_y = self._canvas.winfo_rooty()
        canvas_width = self._canvas.winfo_width()
        canvas_height = self._canvas.winfo_height()

        # Проверяем, находится ли курсор над канвой
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
        for item in self.thumbnails:
            item.thumbnail_label.grid_forget()
            item.caption_label.grid_forget()
        self.thumbnails = []
        self._filtered_thumbnails = []
        self.thumbnail_paths.clear()
        self.selected_paths.clear()  # Очищаем состояние выделения
        self._canvas.configure(scrollregion=self._canvas.bbox(ALL))
        with self._processing_lock:
            self._pending_futures.clear()
            self._is_processing = False

    @abstractmethod
    def _prepare_thumbnail_data(self, source_path: str, click_callback: Optional[Callable[[str], None]] = None) -> Optional[ThumbnailData]:
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
                thumb_data: Optional[ThumbnailData] = future.result()
            except Exception as e:
                print(f"Error processing thumbnail: {e}")
                continue
            if thumb_data is None:
                continue
            try:
                photo = PhotoImage(thumb_data.thumbnail)

                thumbnail_label = Label(self.frame, image=photo)
                thumbnail_label.image = photo  # type: ignore[attr-defined]
                thumbnail_label.grid()

                # Create a label for the caption and set its width to match the thumbnail width
                caption_label = Label(self.frame, wraplength=self.thumbnail_size, background=self._background_color)
                if thumb_data.caption is not None:
                    caption_label.configure(text=thumb_data.caption)
                caption_label.grid(sticky=N)

                # Создаем информацию о файле и элемент миниатюры
                self.thumbnails.append(ThumbnailItem(
                    thumbnail_label=thumbnail_label,
                    caption_label=caption_label,
                    data=thumb_data
                ))
                self.thumbnail_paths.add(thumb_data.path)

                # Создаем обработчик клика, учитывающий модификаторы клавиатуры для множественного выделения
                def selection_click_handler(event: Event, path: str = thumb_data.path) -> None:
                    # Проверяем, нажата ли клавиша Ctrl для множественного выделения
                    if int(event.state) & 0x0004:  # Ctrl нажат
                        self.toggle_thumbnail_selection(path)
                    else:
                        self.select_thumbnail(path)

                    # Вызываем оригинальный обработчик, если он есть
                    if thumb_data.click_callback:
                        thumb_data.click_callback(path)

                # Привязываем обработчик выделения к миниатюре и подписи
                thumbnail_label.bind("<Button-1>", selection_click_handler)  # type: ignore[misc]
                caption_label.bind("<Button-1>", selection_click_handler)  # type: ignore[misc]

            except Exception as e:
                print(f"Error processing thumbnail {thumb_data.path}: {e}")

        # Если есть завершённые задачи, обновляем layout
        if completed:
            with self._processing_lock:
                # Переприменяем фильтр к новым миниатюрам
                self._apply_filter()

                if self._pending_futures:
                    # Базовое обновление без полной сортировки
                    self._canvas.configure(scrollregion=self._canvas.bbox(ALL))
                else:
                    # Полная сортировка, когда все задачи завершены
                    self.sort_thumbnails()
                    self.update()
                    self.master.update()

        # Продолжаем обработку, если есть незавершённые задачи
        with self._processing_lock:
            if self._pending_futures:
                self.after(100, self._process_pending)
            else:
                self._is_processing = False

    def set_sort_control_visibility(self, visible: bool) -> None:
        """
        Показать или скрыть панель управления сортировкой

        :param visible: True для отображения, False для скрытия
        """
        self._show_sort_control = visible
        if visible and not self.control_frame.winfo_ismapped():
            self.control_frame.pack(side=TOP, fill=X, padx=5, pady=5)
        elif not visible and self.control_frame.winfo_ismapped():
            self.control_frame.pack_forget()
