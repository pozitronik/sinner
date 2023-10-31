from tkinter import Label, StringVar,  Frame, X, TOP, NW
from typing import Union, Callable, Any

from customtkinter import CTkSlider

from sinner.gui.controls.FramePosition.BaseFramePosition import BaseFramePosition


class SliderFramePosition(BaseFramePosition, CTkSlider):
    _container = Frame
    _position_label: Label | None = None
    _current_position: StringVar = None
    _cmd: Union[Callable[[float], None], None] = None

    def __init__(self, master: any, **kwargs):
        self._container = Frame(master, borderwidth=2)
        CTkSlider.__init__(self, self._container, **kwargs)
        self._current_position = StringVar()
        self._position_label = Label(master)
        self._position_label.configure(textvariable=self._current_position)
        self.update_position()

    def pack(self, **kwargs) -> Any:
        self._container.pack(fill=X)
        result = CTkSlider.pack(self, **kwargs)
        self._position_label.pack(anchor=NW, side=TOP, expand=False, fill=X, after=self)
        return result

    def pack_forget(self) -> Any:
        self._container.pack_forget()

    def _clicked(self, event=None) -> None:
        CTkSlider._clicked(self, event)
        self.update_position()

    def set(self, output_value: int, from_variable_callback: bool = False) -> None:
        CTkSlider.set(self, output_value, from_variable_callback)
        self.update_position()

    def update_position(self):
        if self._position_label:
            self._current_position.set(f'{self.position}/{self._to}')

    @property
    def to(self) -> int:
        return self._to

    @property
    def position(self) -> int:
        return int(self.get())

    @position.setter
    def position(self, value: int) -> None:
        self.set(value)

    @to.setter
    def to(self, value: int) -> None:
        if value > self.position:
            self.position = value
        self.configure(to=value)

    @property
    def container(self) -> Frame:
        return self._container