from tkinter import Label
from typing import Any, Tuple, Union, Literal

from sinner.gui.controls.ThumbnailWidget.SortField import SortField

# Определяем типы для relief и cursor
ReliefType = Literal["flat", "groove", "raised", "ridge", "solid", "sunken"]
CursorType = Union[str, Tuple[str, str, str], Tuple[str, str]]


class SortButton(Label):
    """Специализированная кнопка для панели сортировки с привязанным полем SortField"""

    field: SortField

    def __init__(self, master: Any, field: SortField, text: str = "", padx: Union[int, Tuple[int, int]] = 0, pady: Union[int, Tuple[int, int]] = 0,
                 relief: ReliefType = "flat", cursor: CursorType = "arrow", **kwargs: Any) -> None:
        """
        Создает кнопку сортировки с привязанным полем

        :param master: Родительский виджет
        :param field: Поле сортировки, связанное с кнопкой
        :param text: Текст кнопки
        :param padx: Отступ по горизонтали
        :param pady: Отступ по вертикали
        :param relief: Стиль рельефа кнопки
        :param cursor: Курсор при наведении
        :param kwargs: Дополнительные параметры для Label
        """
        super().__init__(master, text=text, padx=padx, pady=pady, relief=relief, cursor=cursor, **kwargs)  # type: ignore[arg-type]  # wrong mypy stubs
        self.field = field
