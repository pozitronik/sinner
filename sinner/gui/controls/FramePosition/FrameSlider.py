from tkinter import DISABLED, NORMAL, IntVar
from typing import Any, TypeVar, Type

from customtkinter import CTkSlider

from sinner.gui.controls.FramePosition.BaseFramePosition import BaseFramePosition
from sinner.gui.controls.ProgressIndicator.BaseProgressIndicator import BaseProgressIndicator
from sinner.gui.controls.ProgressIndicator.SegmentedProgressBar import SegmentedProgressBar

T = TypeVar('T', bound=BaseProgressIndicator)


class FrameSlider(CTkSlider, BaseFramePosition):

    def __init__(self, master: Any, progress: Type[T] = SegmentedProgressBar, **kwargs):  # type: ignore[no-untyped-def]
        progress_height = 10

        # Инициализируем базовый слайдер с измененными параметрами
        CTkSlider.__init__(
            self,
            master=master,
            height=20,
            button_corner_radius=1,
            # button_length=2,  # делаем ползунок более узким,
            corner_radius=0,
            border_width=0,
            **kwargs
        )

        self.progress: BaseProgressIndicator = progress(
            master=self.master,
            height=progress_height,
            borderwidth=0,
            border=0,
            colors={0: 'orange', 1: 'yellow', 2: 'green', 3: 'red'}
        )

        self.progress.place_configure(
            in_=self,
            x=0,
            y=self.winfo_reqheight() - progress_height,
            relwidth=1.0,  # занимает всю ширину
            height=progress_height
        )

        self.progress.pass_through = self

    def pack(self, **kwargs) -> Any:  # type: ignore[no-untyped-def]
        result = CTkSlider.pack(self, **kwargs)
        return result

    def pack_forget(self) -> Any:
        self.pack_forget()

    def _clicked(self, event: Any | None = None) -> None:
        CTkSlider._clicked(self, event)

    def set(self, output_value: int, from_variable_callback: bool = False) -> None:
        if self._from_ < self._to:
            if output_value > self._to:
                output_value = self._to
            elif output_value < self._from_:
                output_value = self._from_
        else:
            if output_value < self._to:
                output_value = self._to
            elif output_value > self._from_:
                output_value = self._from_

        self._output_value = self._round_to_step_size(output_value)
        try:
            self._value = (self._output_value - self._from_) / (self._to - self._from_)
        except ZeroDivisionError:
            self._value = 1

        self._draw()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(round(self._output_value) if isinstance(self._variable, IntVar) else self._output_value)
            self._variable_callback_blocked = False

    @property
    def to(self) -> int:
        return self._to

    @to.setter
    def to(self, value: int) -> None:
        if value > self.position:
            self.position = value
        self.configure(to=value)

    @property
    def position(self) -> int:
        return int(self.get())

    @position.setter
    def position(self, value: int) -> None:
        self.set(value)

    def disable(self) -> None:
        CTkSlider.configure(self, True, state=DISABLED)

    def enable(self) -> None:
        CTkSlider.configure(self, True, state=NORMAL)
