from customtkinter import CTkSlider


class NavigateSlider(CTkSlider):

    @property
    def to(self) -> int:
        return self._to

    @property
    def position(self) -> int:
        return int(self.get())
