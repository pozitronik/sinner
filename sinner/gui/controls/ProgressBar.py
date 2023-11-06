from threading import Lock
from tkinter import HORIZONTAL, Misc, BOTH, Label, NW, StringVar, IntVar, LEFT, RIGHT
from tkinter.ttk import Progressbar
from types import TracebackType
from typing import Optional, Type


class ProgressBar:
    maximum: int | None = None
    value: int | None = None
    title: str | None = None
    _variable: IntVar | None = None
    _pb: Progressbar | None = None
    _label: Label | None = None
    _progressVar: StringVar | None = None

    controls_flag: bool = False

    def __init__(self, parent: Misc | None):
        self.parent = parent

    def configure(self, value: int, maximum: int, title: str = "Progress", variable: IntVar | None = None) -> 'ProgressBar':
        self.value = value
        self.maximum = maximum
        self.title = title
        self._variable = variable
        return self

    @property
    def pb(self) -> Progressbar:
        if self._pb is None:
            self._pb = Progressbar(self.parent, orient=HORIZONTAL, mode="determinate", maximum=self.maximum, value=self.value, variable=self._variable)
            self._pb.pack(side=LEFT, expand=True, fill=BOTH)
        return self._pb

    @property
    def progress_var(self) -> StringVar:
        if self._progressVar is None:
            self._progressVar = StringVar(value=self.progress_text)
        return self._progressVar

    @property
    def label(self) -> Label:
        if self._label is None:
            self._label = Label(self.parent, text=self.title, textvariable=self.progress_var)
            self._label.pack(anchor=NW, side=RIGHT, expand=False, fill=BOTH, after=self.pb)
        return self._label

    def create_controls(self):
        if self.controls_flag is False:
            self.controls_flag = True

    def destroy_controls(self) -> None:
        with Lock():
            self.controls_flag = False
            if self._pb:
                self._pb.destroy()
                self._pb = None
            if self._label:
                self._label.destroy()
                self._label = None
            if self._progressVar:
                self._progressVar = None

    def __enter__(self) -> 'ProgressBar':
        if self.parent:
            self.parent.update()
        return self

    def progressbar(self) -> Progressbar:
        return self.pb

    @property
    def pb_value(self) -> int:
        if self.controls_flag:
            try:
                return int(self.pb.cget('value'))
            except Exception:
                pass
        return 0

    @pb_value.setter
    def pb_value(self, value: int) -> None:
        if self.controls_flag:
            self.pb['value'] = value

    @property
    def progress_text(self) -> str:
        return f"{self.title}: {int(self.pb_value)}/{self.maximum}"

    def update(self, value: int = 1) -> None:
        if not self.controls_flag:
            self.create_controls()
        try:
            self.progress_var.set(self.progress_text)
        except Exception:
            pass
        self.pb_value += value
        if self.parent:
            self.parent.update()

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
        self.destroy_controls()
