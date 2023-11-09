from tkinter import SOLID, Misc, Toplevel, Label, Event


class Tooltip:
    widget: Misc
    text: str
    tooltip: Toplevel | None

    def __init__(self, widget: Misc, text: str):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    # noinspection PyUnusedLocal
    def show_tooltip(self, event: Event) -> None:  # type: ignore[type-arg]
        x, y, _, _ = self.widget.bbox()
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = Label(self.tooltip, text=self.text, background="lightyellow", relief=SOLID)
        label.pack()

    # noinspection PyUnusedLocal
    def hide_tooltip(self, event: Event) -> None:  # type: ignore[type-arg]
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
