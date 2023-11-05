from tkinter import HORIZONTAL, Misc, BOTTOM, BOTH, Label, NW, StringVar
from tkinter.ttk import Progressbar


class ProgressBar:
    maximum: int | None = None
    length: int | None = None
    title: str | None = None
    pb: Progressbar | None = None
    label: Label | None = None
    progressVar: StringVar | None = None

    def __init__(self, parent: Misc | None):
        self.parent = parent

    def set_parameters(self, maximum: int, length: int = 400, title: str = "Progress") -> 'ProgressBar':
        self.maximum = maximum
        self.title = title
        self.length = length
        return self

    def __enter__(self) -> 'ProgressBar':
        self.pb = Progressbar(self.parent, orient=HORIZONTAL, mode="determinate", maximum=self.maximum, length=self.length)
        self.pb.pack(side=BOTTOM, expand=True, fill=BOTH)
        self.progressVar = StringVar(value=self.progress_text)
        self.label = Label(self.parent, text=self.title, textvariable=self.progressVar)
        self.label.pack(anchor=NW, side=BOTTOM, expand=False, fill=BOTH, after=self.pb)
        if self.parent:
            self.parent.update()
        return self

    @property
    def progress_text(self) -> str:
        return f"{self.title}: {int(self.pb['value'])}/{self.maximum}"

    def update(self, value: int = 1) -> None:
        if self.pb:
            self.progressVar.set(self.progress_text)
            self.pb["value"] += value
            if self.parent:
                self.parent.update()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self.pb:
            self.pb.destroy()
        if self.label:
            self.label.destroy()
        return False
