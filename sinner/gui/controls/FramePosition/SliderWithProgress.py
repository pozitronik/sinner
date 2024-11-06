from customtkinter import CTkSlider
from typing import Any

from sinner.gui.controls.ProgressIndicator.SegmentedProgressBar import SegmentedProgressBar


class SliderWithProgress(CTkSlider):
    def __init__(self, master: Any, **kwargs
                 ):
        # Настраиваем увеличенную высоту для размещения прогрессбара
        progress_height = 10
        slider_height = 16  # стандартная высота ползунка
        total_height = max(progress_height + 6, slider_height)  # 6 пикселей для отступов

        # Инициализируем базовый слайдер с измененными параметрами
        super().__init__(
            master,
            height=total_height,
            button_length=1,  # делаем ползунок более узким
            **kwargs
        )

        # Создаем и размещаем прогрессбар
        self.progress = SegmentedProgressBar(
            self,
            height=progress_height,
            colors={0: '', 1: 'yellow', 2: 'green', 3: 'red'}
        )

        # Размещаем прогрессбар по центру под ползунком
        progress_y = (total_height - progress_height) // 2
        self.progress.place(
            x=0,
            y=progress_y,
            relwidth=1.0,  # занимает всю ширину
            height=progress_height
        )

        # Настраиваем отображение
        self._configure_appearance()

    def _configure_appearance(self) -> None:
        """Настройка внешнего вида компонента"""
        # Делаем фон слайдера прозрачным, так как будет виден прогрессбар
        self.configure(
            button_corner_radius=4,  # более острые углы ползунка
            corner_radius=0,  # прямые углы основного виджета
            button_color="gray60",  # цвет ползунка
            button_hover_color="gray50",
        )

        # Скрываем стандартный трек слайдера
        # self._canvas.configure(bg='transparent')

    # def configure(self, require_redraw=False, **kwargs: Any) -> None:
    #     """
    #     Настройка параметров виджета
    #
    #     Расширяет стандартный метод для поддержки параметров прогрессбара
    #     """
    #     # Выделяем параметры для прогрессбара
    #     progress_kwargs = {}
    #     for key in list(kwargs.keys()):
    #         if key.startswith('progress_'):
    #             progress_kwargs[key[9:]] = kwargs.pop(key)
    #
    #     # Настраиваем прогрессбар если есть параметры для него
    #     if progress_kwargs:
    #         for key, value in progress_kwargs.items():
    #             if hasattr(self.progress, key):
    #                 setattr(self.progress, key, value)
    #
    #     # Передаем остальные параметры базовому классу
    #     super().configure(**kwargs)
