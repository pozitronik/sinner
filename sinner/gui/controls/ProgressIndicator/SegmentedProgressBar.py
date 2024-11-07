import asyncio
import tkinter as tk
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from queue import Queue
from threading import Lock
from typing import List, Dict, Optional, Callable

from sinner.gui.controls.ProgressIndicator.BaseProgressIndicator import BaseProgressIndicator

DEFAULT_SEGMENT_COLOR = 'blue'


@dataclass
class UpdateCommand:
    """Команда обновления сегмента"""
    index: int
    value: int
    callback: Optional[Callable[[], None]] = None


class SegmentedProgressBar(BaseProgressIndicator, tk.Canvas):
    _pass_through: tk.Widget | None = None

    def __init__(self, master: tk.Misc | None, segments: int = 100, width: int = 0, height: int = 10, min_visible_width: int = 0, colors: Dict[int, str] | None = None, **kwargs):  # type: ignore[no-untyped-def]
        """
        Создает сегментированный прогресс-бар

        Args:
            master: родительский виджет tkinter
            segments: количество сегментов
            width: общая ширина в пикселях (0 для автоматического размера)
            height: высота в пикселях (0 для автоматического размера)
            min_visible_width: минимальная видимая ширина группы сегментов в пикселях
            colors: словарь соответствия значений цветам (например {0: 'white', 1: 'blue'})
        """
        kwargs['highlightthickness'] = 0  # Убирает внешнюю рамку фокуса
        kwargs['bd'] = 0  # Убирает бордюр
        super().__init__(master, width=width, height=height, **kwargs)

        self.states: List[int] = []
        self.segment_width: float = 0
        self.segments: int = 0
        self.width: int = width
        self.height: int = height
        self.colors: Dict[int, str] = colors or {0: 'white', 1: DEFAULT_SEGMENT_COLOR}
        self.min_visible_width: int = min_visible_width
        self.auto_width: bool = (width == 0)
        self.auto_height: bool = (height == 0)

        # Список для хранения идентификаторов сегментов
        self.segment_ids: List[int] = []

        # Механизмы синхронизации
        self._states_lock = Lock()
        self._update_queue: Queue[UpdateCommand] = Queue()
        self._thread_pool = ThreadPoolExecutor(max_workers=1)
        self._redraw_pending = False

        # Инициализация сегментов
        self.set_segments(segments)

        # Привязываем обработчик изменения размера
        self.bind('<Configure>', self._on_resize)

        # Запускаем обработчик очереди обновлений
        self.after(10, self._process_updates)

    def _process_updates(self) -> None:
        """Обработчик очереди обновлений"""
        try:
            while not self._update_queue.empty():
                command = self._update_queue.get_nowait()
                with self._states_lock:
                    self.states[command.index] = command.value
                if not self._redraw_pending:
                    self._redraw_pending = True
                    self.after_idle(self._do_redraw)
                if command.callback:
                    self.after_idle(command.callback)
        finally:
            # Планируем следующую проверку
            self.after(10, self._process_updates)

    def _do_redraw(self) -> None:
        """Выполняет отложенную перерисовку"""
        try:
            with self._states_lock:
                self._redraw()
        finally:
            self._redraw_pending = False

    def _on_resize(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        """Обработчик изменения размера виджета"""
        if self.auto_width or self.auto_height:
            self.update_size()

    def update_size(self) -> None:
        """Обновляет размеры виджета и пересчитывает сегменты"""
        if self.auto_width:
            self.width = self.winfo_width()
        if self.auto_height:
            self.height = self.winfo_height()

        if self.segments > 0:
            self.segment_width = self.width / self.segments

        # Удаляем все существующие элементы
        self.delete("all")
        self.segment_ids.clear()

        # Создаем фон
        self.create_rectangle(0, 0, self.width, self.height,
                              fill='blue', outline='red',
                              tags="background")

        # Создаем сегменты заново с новыми размерами
        for i in range(self.segments):
            x1 = i * self.segment_width
            x2 = (i + 1) * self.segment_width
            segment_id = self.create_rectangle(
                x1, 0, x2, self.height,
                fill=self.colors.get(self.states[i], DEFAULT_SEGMENT_COLOR),
                outline='',
                tags=f"segment_{i}"
            )
            self.segment_ids.append(segment_id)

    def set_segments(self, segments: int) -> None:
        """
        Изменяет количество сегментов и сбрасывает их состояния

        Args:
            segments: новое количество сегментов
        """
        if segments <= 0:
            raise ValueError("Number of segments must be positive")

        self.segments = segments
        self.segment_width = self.width / segments if self.width > 0 else 0

        # Сброс состояний
        self.states = [0] * segments

        # Пересоздаем сегменты
        self.update_size()

    def update_states(self, states: List[int]) -> None:
        """Обновляет состояния сегментов и перерисовывает их"""
        if len(states) != self.segments:
            raise ValueError(f"Expected {self.segments} states, got {len(states)}")

        self.states = states.copy()
        self._redraw()

    def set_segment_value(self, index: int, value: int, callback: Optional[Callable[[], None]] = None) -> None:
        """
        Устанавливает значение для определенного сегмента

        Args:
            index: индекс сегмента (0-based)
            value: новое значение сегмента
            callback: функция, вызываемая после применения обновления
        """
        if not 0 <= index < self.segments:
            raise ValueError(f"Index {index} out of range [0, {self.segments - 1}]")

        self._update_queue.put(UpdateCommand(index, value, callback))

    async def set_segment_value_async(self, index: int, value: int) -> None:
        """
        Асинхронно устанавливает значение сегмента

        Args:
            index: индекс сегмента (0-based)
            value: новое значение сегмента
        """
        if not 0 <= index < self.segments:
            raise ValueError(f"Index {index} out of range [0, {self.segments - 1}]")

        future: Future[None] = asyncio.Future()

        def callback() -> None:
            future.set_result(None)

        self.set_segment_value(index, value, callback)
        await future

    def set_segment_values(self, indexes: List[int], value: int, reset: bool = True) -> None:
        """
        Устанавливает заданное значение для списка сегментов

        Args:
            indexes: список индексов сегментов
            value: значение для установки
            reset: если True, сначала сбрасывает все сегменты в начальное состояние (0)
        """
        # Проверяем корректность индексов
        if not indexes:
            return
        if min(indexes) < 0 or max(indexes) >= self.segments:
            raise ValueError(f"Segment index out of range [0, {self.segments - 1}]")

        def update() -> None:
            # Сбрасываем состояния если нужно
            if reset:
                with self._states_lock:
                    self.states = [0] * self.segments

            # Обновляем состояния
            for index in indexes:
                self._update_queue.put(UpdateCommand(index, value))

        # Выполняем обновление в главном потоке
        self.after_idle(update)

    def _redraw(self) -> None:
        """Перерисовывает все сегменты с учетом минимальной видимой ширины"""
        if self.width == 0 or self.height == 0:
            return  # Пропускаем отрисовку, если размеры еще не определены

        # Группируем последовательные сегменты одного цвета
        groups = []
        current_value = self.states[0]
        current_start = 0

        for i, value in enumerate(self.states[1:], 1):
            if value != current_value:
                groups.append((current_start, i, current_value))
                current_value = value
                current_start = i

        # Добавляем последнюю группу
        groups.append((current_start, len(self.states), current_value))

        # Обновляем цвета сегментов для каждой группы
        for start, end, value in groups:
            # Вычисляем координаты группы
            x1 = start * self.segment_width
            x2 = end * self.segment_width

            # Проверяем, достаточно ли группа широкая для отображения
            if x2 - x1 >= self.min_visible_width:
                # Обновляем цвета для всех сегментов в группе
                for i in range(start, end):
                    if i < len(self.segment_ids):  # Проверка на всякий случай
                        segment_id = self.segment_ids[i]
                        self.itemconfig(segment_id,
                                        fill=self.colors.get(value, DEFAULT_SEGMENT_COLOR))

    @property
    def pass_through(self) -> tk.Widget | None:
        return self._pass_through

    @pass_through.setter
    def pass_through(self, value: tk.Widget | None) -> None:
        self._pass_through = value
        if self._pass_through:
            # Привязываем события мыши
            self.bind('<Button-1>', self._handle_mouse_event)
            self.bind('<ButtonRelease-1>', self._handle_mouse_event)
            self.bind('<Button-2>', self._handle_mouse_event)
            self.bind('<ButtonRelease-2>', self._handle_mouse_event)
            self.bind('<Button-3>', self._handle_mouse_event)
            self.bind('<ButtonRelease-3>', self._handle_mouse_event)
            self.bind('<Motion>', self._handle_mouse_event)
            self.bind('<B1-Motion>', self._handle_mouse_event)
            self.bind('<B2-Motion>', self._handle_mouse_event)
            self.bind('<B3-Motion>', self._handle_mouse_event)
            self.bind('<Enter>', self._handle_mouse_event)
            self.bind('<Leave>', self._handle_mouse_event)

    def _handle_mouse_event(self, event: tk.Event) -> str:  # type: ignore[type-arg]
        """
            Транслирует событие мыши в CTkSlider
            Изначально код задумывался для трансляции любых событий в любой виджет, но
            оказалось, что слайдер имеет кастомную обработку, и пришлось это учесть.
        """
        if not self.pass_through or not hasattr(self._pass_through, '_clicked'):
            return ""

        # Конвертируем координаты
        abs_x = self.winfo_rootx() + event.x
        abs_y = self.winfo_rooty() + event.y
        rel_x = abs_x - self._pass_through.winfo_rootx()
        rel_y = abs_y - self._pass_through.winfo_rooty()

        # Создаем новое событие
        new_event = tk.Event()
        new_event.x = rel_x
        new_event.y = rel_y
        new_event.x_root = event.x_root
        new_event.y_root = event.y_root
        new_event.type = event.type
        new_event.widget = self._pass_through

        # Словарь соответствия событий методам слайдера
        handlers = {
            tk.EventType.ButtonPress: '_clicked',
            tk.EventType.Motion: '_motion',
            tk.EventType.ButtonRelease: '_released'
        }

        # Вызываем соответствующий метод, если он есть
        if event.type in handlers and hasattr(self._pass_through, handlers[event.type]):
            getattr(self._pass_through, handlers[event.type])(new_event)

            return "break"
