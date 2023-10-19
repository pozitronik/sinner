from customtkinter import CTkSlider


class NavigateSlider(CTkSlider):

    @property
    def to(self) -> int:
        return self._to