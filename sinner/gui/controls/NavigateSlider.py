from tkinter import Label, StringVar, NE, RIGHT
from typing import Union, Callable

from customtkinter import CTkSlider


class NavigateSlider(CTkSlider):
    _position_label: Label | None = None
    _current_position: StringVar = None
    _cmd: Union[Callable[[float], None], None] = None

    def __init__(self, master: any, **kwargs):
        super().__init__(master, **kwargs)
        self._current_position = StringVar()
        self._position_label = Label(master)
        self._position_label.pack(anchor=NE, side=RIGHT)
        self._position_label.configure(textvariable=self._current_position)

    def _clicked(self, event=None) -> None:
        super()._clicked(event)
        if self._position_label:
            self._current_position.set(f'{self.position}/{self._to}')

    @property
    def to(self) -> int:
        return self._to

    @property
    def position(self) -> int:
        return int(self.get())

    @position.setter
    def position(self, value: int):
        self.set(value)

    @to.setter
    def to(self, value: int) -> None:
        if value > self.position:
            self.position = value
        self.configure(to=value)
