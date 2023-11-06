from tkinter import HORIZONTAL, Misc, BOTTOM, BOTH, Label, NW, StringVar, IntVar
from tkinter.ttk import Progressbar


class ProgressBar:
    maximum: int | None = None
    value: int | None = None
    title: str | None = None
    variable: IntVar | None = None
    pb: Progressbar | None = None
    label: Label | None = None
    progressVar: StringVar | None = None

    def __init__(self, parent: Misc | None):
        self.parent = parent

    def configure(self, value: int, maximum: int, title: str = "Progress", variable: IntVar | None = None) -> 'ProgressBar':
        self.value = value
        self.maximum = maximum
        self.title = title
        self.variable = variable
        return self

    def create_controls(self) -> None:
        self.pb = Progressbar(self.parent, orient=HORIZONTAL, mode="determinate", maximum=self.maximum, value=self.value, variable=self.variable)
        self.pb.pack(side=BOTTOM, expand=True, fill=BOTH)
        self.progressVar = StringVar(value=self.progress_text)
        self.label = Label(self.parent, text=self.title, textvariable=self.progressVar)
        self.label.pack(anchor=NW, side=BOTTOM, expand=False, fill=BOTH, after=self.pb)

    def destroy_controls(self) -> None:
        if self.pb:
            self.pb.destroy()
        if self.label:
            self.label.destroy()

    def __enter__(self) -> 'ProgressBar':
        self.create_controls()
        if self.parent:
            self.parent.update()
        return self

    def progressbar(self) -> Progressbar:
        self.create_controls()
        return self.pb

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
        self.destroy_controls()
        return False
