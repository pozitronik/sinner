from tkinter import Frame, BOTH, X, BOTTOM, Misc
from typing import Dict, Any

from sinner.gui.controls.TextBox import TextBox


#  a simple status bar stub.
class SimpleStatusBar(Frame):
    items: Dict[str, Any] = {}
    text_box: TextBox

    def __init__(self, master: Misc | None = None, cnf: Dict[str, Any] | None = None) -> None:
        if cnf is None:
            cnf = {}
        super().__init__(master, cnf)
        self.text_box: TextBox = TextBox(self)
        self.text_box.configure(state='readonly')

    def pack(self) -> None:  # type: ignore[override]   # needs to be rewritten
        super().pack(fill=X)
        self.text_box.pack(side=BOTTOM, expand=True, fill=BOTH)

    def update_text(self) -> None:
        self.text_box.set_text(self.get_status_text())

    def get_status_text(self) -> str:
        result: str = ''
        for name, value in self.items.items():
            result += f"{name}: {value}; "
        return result

    def set_item(self, name: str, value: Any) -> None:
        self.items[name] = value
        self.update_text()
