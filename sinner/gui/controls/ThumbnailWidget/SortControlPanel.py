from tkinter import Frame, Label, LEFT
from typing import Callable

from sinner.gui.controls.ThumbnailWidget.SortField import SortField


class SortControlPanel(Frame):
    """Панель управления сортировкой для виджета эскизов"""

    def __init__(self, master, on_sort_changed: Callable[[SortField, bool], None], **kwargs):
        """
        Создает панель управления сортировкой

        :param master: Родительский виджет
        :param on_sort_changed: Функция обратного вызова при изменении сортировки.
                Принимает поле сортировки и флаг порядка (True - по возрастанию)
        :param kwargs: Дополнительные параметры для Frame
        """
        super().__init__(master, **kwargs)

        # Функция обратного вызова
        self._on_sort_changed = on_sort_changed

        # Текущее состояние сортировки
        self._current_field = SortField.NAME  # По умолчанию - имя файла
        self._is_ascending = True

        # Создаем элементы управления
        self._create_widgets()

    def _create_widgets(self):
        """Создает и размещает элементы управления"""
        # Метка "Сортировка:"
        sort_label = Label(self, text="Sort by:")
        sort_label.pack(side=LEFT, padx=(0, 5))

        # Создаем выпадающее меню для выбора поля сортировки
        self.field_menu = Frame(self)
        self.field_menu.pack(side=LEFT, padx=(0, 5))

        # Переменная для хранения текущего выделенного поля
        self.field_buttons = {}

        # Создаем кнопки для каждого поля сортировки
        for field in SortField:
            button = Label(self.field_menu, text=field.value, padx=5, pady=2,
                           relief="raised" if field == self._current_field else "flat",
                           cursor="hand2")
            button.field = field
            button.bind("<Button-1>", self._on_field_selected)
            button.pack(side=LEFT)
            self.field_buttons[field] = button

        # Кнопка для переключения порядка сортировки
        order_text = "↑" if self._is_ascending else "↓"
        self.order_button = Label(self, text=order_text, padx=5, pady=2,
                                  cursor="hand2", relief="raised")
        self.order_button.pack(side=LEFT)
        self.order_button.bind("<Button-1>", self._toggle_order)

    def _toggle_order(self, event=None):  # type: ignore[type-arg]
        """Переключает порядок сортировки и обновляет UI"""
        self._is_ascending = not self._is_ascending

        # Обновляем текст кнопки
        self.order_button.config(text="↑" if self._is_ascending else "↓")

        # Вызываем функцию обратного вызова
        self._trigger_sort_changed()

    def _on_field_selected(self, event):
        """Обработчик выбора поля сортировки"""
        # Получаем кнопку, на которую нажали
        button = event.widget
        field = button.field

        # Если поле уже выбрано - просто переключаем порядок
        if field == self._current_field:
            self._toggle_order()
            return

        # Меняем выделение кнопок
        self.field_buttons[self._current_field].config(relief="flat")
        button.config(relief="raised")

        # Обновляем текущее поле
        self._current_field = field

        # Вызываем функцию обратного вызова
        self._trigger_sort_changed()

    def _trigger_sort_changed(self):
        """Вызывает функцию обратного вызова с текущими параметрами сортировки"""
        if self._on_sort_changed:
            self._on_sort_changed(self._current_field, self._is_ascending)

    def get_current_sort(self) -> tuple[SortField, bool]:
        """Возвращает текущие параметры сортировки"""
        return self._current_field, self._is_ascending

    def set_sort(self, field: SortField, ascending: bool = True):
        """
        Устанавливает параметры сортировки без вызова обратного вызова

        :param field: Поле сортировки
        :param ascending: True для сортировки по возрастанию, False - по убыванию
        """
        # Если поле меняется, обновляем выделение кнопок
        if field != self._current_field:
            self.field_buttons[self._current_field].config(relief="flat")
            self.field_buttons[field].config(relief="raised")

        self._current_field = field
        self._is_ascending = ascending

        # Обновляем кнопку порядка
        self.order_button.config(text="↑" if ascending else "↓")
