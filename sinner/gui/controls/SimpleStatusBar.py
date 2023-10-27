from tkinter import Frame, BOTH, X, BOTTOM
from typing import Dict, Any

from sinner.gui.controls.TextBox import TextBox, READONLY


#  a simple status bar stub.
class SimpleStatusBar(Frame):
    items: Dict[str, Any] = {}
    text_box: TextBox

    def __init__(self, master=None, cnf=None):
        if cnf is None:
            cnf = {}
        super().__init__(master, cnf)
        self.text_box: TextBox = TextBox(self)
        self.text_box.configure(state=READONLY)

    def pack(self) -> None:
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
