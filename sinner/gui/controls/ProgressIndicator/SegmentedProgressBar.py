import tkinter as tk
from typing import List, Dict

from sinner.gui.controls.ProgressIndicator.BaseProgressIndicator import BaseProgressIndicator

DEFAULT_SEGMENT_COLOR = 'blue'


class SegmentedProgressBar(BaseProgressIndicator, tk.Canvas):
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

        # Инициализация сегментов
        self.set_segments(segments)

        # Привязываем обработчик изменения размера
        self.bind('<Configure>', self._on_resize)

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
                              fill='white', outline='gray',
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

    def set_segment_value(self, index: int, value: int) -> None:
        """
        Устанавливает значение для определенного сегмента

        Args:
            index: индекс сегмента (0-based)
            value: новое значение сегмента
        """
        if not 0 <= index < self.segments:
            raise ValueError(f"Index {index} out of range [0, {self.segments - 1}]")

        self.states[index] = value
        self._redraw()

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

        # Сбрасываем состояния если нужно
        if reset:
            self.states = [0] * self.segments

        # Обновляем состояния
        for index in indexes:
            self.states[index] = value

        # Перерисовываем один раз после всех обновлений
        self._redraw()

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
