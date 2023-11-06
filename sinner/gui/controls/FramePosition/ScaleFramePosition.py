from tkinter import Scale
from typing import Any

from sinner.gui.controls.FramePosition.BaseFramePosition import BaseFramePosition


class ScaleFramePosition(BaseFramePosition, Scale):

    def disable(self):
        pass

    def enable(self):
        pass

    def __init__(self, master=None, cnf=None, **kw):
        if cnf is None:
            cnf = {}
        Scale.__init__(self, master=master, cnf=cnf, **kw)
        BaseFramePosition.__init__(self)

    def pack(self, **kwargs) -> Any:
        return Scale.pack(self, **kwargs)

    @property
    def position(self) -> int:
        return int(self.get())

    @position.setter
    def position(self, value: int):
        self.set(value)

    @property
    def to(self) -> int:
        return self.to

    @to.setter
    def to(self, value: int) -> None:
        if value > self.position:
            self.position = value
        self.configure(to=value)

    def set(self, output_value: int, from_variable_callback: bool = False) -> None:
        super().set(output_value, from_variable_callback)
        pass
