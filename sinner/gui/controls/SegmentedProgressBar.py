import tkinter as tk
from typing import List, Dict


class SegmentedProgressBar(tk.Canvas):
    def __init__(
            self,
            master,
            segments: int = 100,
            width: int = 400,
            height: int = 30,
            min_visible_width: int = 2,
            colors: Dict[int, str] = None,
            **kwargs
    ):
        """
        Создает сегментированный прогресс-бар

        Args:
            master: родительский виджет tkinter
            segments: количество сегментов
            width: общая ширина в пикселях
            height: высота в пикселях
            min_visible_width: минимальная видимая ширина группы сегментов в пикселях
            colors: словарь соответствия значений цветам (например {0: 'white', 1: 'blue'})
        """
        super().__init__(master, width=width, height=height, **kwargs)

        self.states = None
        self.segment_width = None
        self.segments = None
        self.width = width
        self.colors = colors or {0: 'white', 1: 'blue'}
        self.min_visible_width = min_visible_width

        # Инициализация сегментов
        self.set_segments(segments)

        # Создание фона
        self.create_rectangle(0, 0, width, height, fill='white', outline='gray')

    def set_segments(self, segments: int) -> None:
        """
        Изменяет количество сегментов и сбрасывает их состояния

        Args:
            segments: новое количество сегментов
        """
        if segments <= 0:
            raise ValueError("Number of segments must be positive")

        self.segments = segments
        self.segment_width = self.width / segments
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
