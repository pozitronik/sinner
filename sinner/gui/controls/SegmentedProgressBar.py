import tkinter as tk
from typing import List, Dict


class SegmentedProgressBar(tk.Canvas):
    def __init__(self, master: tk.Misc | None, segments: int = 100, width: int = 0, height: int = 10, min_visible_width: int = 1, colors: Dict[int, str] | None = None, **kwargs):  # type: ignore[no-untyped-def]
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
        self.colors: Dict[int, str] = colors or {0: 'white', 1: 'blue'}
        self.min_visible_width: int = min_visible_width
        self.auto_width: bool = (width == 0)
        self.auto_height: bool = (height == 0)

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

        # Обновляем фон и сегменты
        self.delete("all")  # Удаляем все фигуры
        self.create_rectangle(0, 0, self.width, self.height, fill='white', outline='gray')
        self._redraw()

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
        self._redraw()

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

    def _redraw(self) -> None:
        """Перерисовывает все сегменты с учетом минимальной видимой ширины"""
        # Очищаем все, кроме фона
        self.delete("segment")

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

        # Отрисовываем группы
        for start, end, value in groups:
            # Вычисляем координаты группы
            x1 = start * self.segment_width
            x2 = end * self.segment_width

            # Проверяем, достаточно ли группа широкая для отображения
            if x2 - x1 >= self.min_visible_width:
                self.create_rectangle(
                    x1, 0, x2, self.winfo_height(),
                    fill=self.colors.get(value, 'gray'),
                    outline='',
                    tags="segment"
                )
