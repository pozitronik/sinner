from customtkinter import CTkSlider


class NavigateSlider(CTkSlider):

    @property
    def to(self) -> int:
        return self._to

    @property
    def position(self) -> int:
        return int(self.get())

    @position.setter
    def position(self, value: int):
        self.set(value)

    @to.setter
    def to(self, value: int) -> None:
        if value > self.position:
            self.position = value
        self.configure(to=value)
