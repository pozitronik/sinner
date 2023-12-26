# a progressbar with display label
from threading import Lock
from tkinter import Misc, Label, StringVar, HORIZONTAL, BOTH, RIGHT, LEFT, NW
from tkinter.ttk import Progressbar
from typing import Dict


class ProgressBar:
    _title: str
    _parent: Misc
    _pb: Progressbar
    _label: Label
    _progressVar: StringVar

    _exists: bool = False

    def __init__(self, parent: Misc, max_value: float, initial_value: float, title: str = "Progress"):
        self._title = title
        self._parent = parent
        self._pb = Progressbar(self._parent, orient=HORIZONTAL, mode="determinate", maximum=max_value, value=initial_value)
        self._progressVar = StringVar(value=self.progress_text)
        self._label = Label(self._parent, textvariable=self._progressVar)
        self._pb.pack(side=LEFT, expand=True, fill=BOTH)
        self._label.pack(anchor=NW, side=RIGHT, expand=False, fill=BOTH, after=self._pb)
        self._exists = True

    @property
    def value(self) -> float:
        if self._exists:
            return float(self._pb.cget('value'))
        return 0

    @value.setter
    def value(self, value: float) -> None:
        if self._exists:
            self._pb.configure(value=value)

    @property
    def maximum(self) -> float:
        if self._exists:
            return float(self._pb.cget('maximum'))
        return 0

    @maximum.setter
    def maximum(self, value: float) -> None:
        if self._exists:
            self._pb.configure(maximum=value)

    @property
    def progress_text(self) -> str:
        return f"{self._title}: {int(self.value)}/{int(self.maximum)}"

    def destroy(self) -> None:
        self._exists = False
        self._pb.destroy()
        self._label.destroy()
        if self._parent:
            self._parent.update()

    def update(self) -> None:
        if self._exists:
            self._progressVar.set(self.progress_text)
            self._pb.update()


#  there are many progressbars can be shown at the same time, so class tries to handle them in an easy way
class ProgressBarManager:
    _parent: Misc
    _bars: Dict[str, ProgressBar] = {}

    def __init__(self, parent: Misc):
        self._parent = parent

    def get(self, name: str, max_value: float | None = None, initial_value: float | None = None) -> ProgressBar:
        if name in self._bars:
            return self._bars[name]
        if max_value is None:
            max_value = 100
        if initial_value is None:
            initial_value = 0
        self._bars[name] = ProgressBar(self._parent, max_value=max_value, initial_value=initial_value, title=name)
        return self._bars[name]

    def done(self, name: str) -> bool:
        with Lock():
            if name in self._bars:
                self._bars[name].destroy()
                del self._bars[name]
                return True
        return False

    def update(self, name: str, value: float | None = None, max_value: float | None = None) -> None:
        self._parent.after(0, self._update, name, value, max_value)
        self._parent.update()

    def _update(self, name: str, value: float | None = None, max_value: float | None = None) -> ProgressBar:
        bar = self.get(name, max_value=max_value, initial_value=value)
        if value is None:
            bar.value += 1
        else:
            bar.value = value
        if max_value is not None:
            bar.maximum = max_value
        bar.update()
        return bar
