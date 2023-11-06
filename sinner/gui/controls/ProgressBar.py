from threading import Lock
from tkinter import HORIZONTAL, Misc, BOTH, Label, NW, StringVar, IntVar, LEFT, RIGHT
from tkinter.ttk import Progressbar


class ProgressBar:
    maximum: int | None = None
    value: int | None = None
    title: str | None = None
    variable: IntVar | None = None
    pb: Progressbar | None = None
    label: Label | None = None
    progressVar: StringVar | None = None

    controls_flag: bool = False

    def __init__(self, parent: Misc | None):
        self.parent = parent

    def configure(self, value: int, maximum: int, title: str = "Progress", variable: IntVar | None = None) -> 'ProgressBar':
        self.value = value
        self.maximum = maximum
        self.title = title
        self.variable = variable
        return self

    def create_controls(self) -> None:
        with Lock():
            if not self.controls_flag:
                self.controls_flag = True
                self.pb = Progressbar(self.parent, orient=HORIZONTAL, mode="determinate", maximum=self.maximum, value=self.value, variable=self.variable)
                self.pb.pack(side=LEFT, expand=True, fill=BOTH)
                self.progressVar = StringVar(value=self.progress_text)
                self.label = Label(self.parent, text=self.title, textvariable=self.progressVar)
                self.label.pack(anchor=NW, side=RIGHT, expand=False, fill=BOTH, after=self.pb)

    def destroy_controls(self) -> None:
        with Lock():
            if self.controls_flag:
                self.controls_flag = False
                self.pb.destroy()
                self.pb = None
                self.label.destroy()
                self.label = None
                self.progressVar = None

    def __enter__(self) -> 'ProgressBar':
        self.create_controls()
        if self.parent:
            self.parent.update()
        return self

    def progressbar(self) -> Progressbar:
        self.create_controls()
        return self.pb

    @property
    def pb_value(self) -> int:
        if self.controls_flag:
            try:
                return int(self.pb.cget('value'))
            except Exception:
                print("wtw")
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
            self.progressVar.set(self.progress_text)
        except Exception:
            print("wtf")
        self.pb_value += value
        if self.parent:
            self.parent.update()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.destroy_controls()
        return False
