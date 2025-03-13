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

        # Создаем фрейм для кнопок полей сортировки
        self.field_menu = Frame(self)
        self.field_menu.pack(side=LEFT)

        # Словарь для хранения кнопок
        self.field_buttons = {}

        # Создаем кнопки для каждого поля сортировки
        for field in SortField:
            # Определяем текст с индикатором для текущего поля
            button_text = field.value
            if field == self._current_field:
                button_text += " " + ("↑" if self._is_ascending else "↓")

            button = Label(self.field_menu, text=button_text, padx=5, pady=2,
                           relief="raised" if field == self._current_field else "flat",
                           cursor="hand2")
            button.field = field
            button.bind("<Button-1>", self._on_field_selected)
            button.pack(side=LEFT)
            self.field_buttons[field] = button

    def _on_field_selected(self, event):
        """Обработчик выбора поля сортировки"""
        # Получаем кнопку, на которую нажали
        button = event.widget
        field = button.field

        # Если поле уже выбрано - просто переключаем порядок
        if field == self._current_field:
            self._is_ascending = not self._is_ascending
            button.config(text=f"{field.value} {'↑' if self._is_ascending else '↓'}")
        else:
            # Сбрасываем текст предыдущей кнопки
            old_button = self.field_buttons[self._current_field]
            old_button.config(text=self._current_field.value, relief="flat")

            # Обновляем текущее поле
            self._current_field = field

            # Выделяем новую кнопку и добавляем индикатор
            button.config(text=f"{field.value} {'↑' if self._is_ascending else '↓'}", relief="raised")

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
        # Если что-то изменилось, обновляем интерфейс
        if field != self._current_field or ascending != self._is_ascending:
            # Сбрасываем текст предыдущей кнопки
            if field != self._current_field:
                old_button = self.field_buttons[self._current_field]
                old_button.config(text=self._current_field.value, relief="flat")

            # Обновляем текущие значения
            self._current_field = field
            self._is_ascending = ascending

            # Обновляем текст и выделение кнопки
            button = self.field_buttons[field]
            button.config(text=f"{field.value} {'↑' if ascending else '↓'}", relief="raised")