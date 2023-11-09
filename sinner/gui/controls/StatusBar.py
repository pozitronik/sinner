from tkinter import Frame, BOTTOM, Misc, X, EW
from typing import Dict

from sinner.gui.controls.TextBox import TextBox
from sinner.gui.controls.Tooltip import Tooltip


class StatusBar(Frame):
    cells: Dict[str, TextBox]

    def __init__(self, master: Misc | None, items: Dict[str, str] | None = None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(side=BOTTOM, expand=True, fill=X)
        self.cells = {}
        if items is not None:  # there's initial items
            self.grid_columnconfigure(len(items))
            for name, value in items.items():
                self.create_cell(name, value)

    def item(self, name: str, value: str, span: int = 1) -> TextBox:
        if name in self.cells:
            cell = self.cells[name]
            cell.set_text(value)
        else:
            cell = self.create_cell(name, value, span)
        return cell

    def create_cell(self, name: str, value: str, span: int = 1) -> TextBox:
        self.grid_columnconfigure(len(self.cells), weight=1)
        cell = TextBox(self, state="readonly")
        cell.grid(row=0, column=len(self.cells), columnspan=span, sticky=EW)
        cell.set_text(value)
        self.cells[name] = cell
        Tooltip(cell, text=name)
        return cell

    def remove_item(self, name: str) -> None:
        if name in self.cells:
            cell = self.cells.pop(name)
            cell.destroy()
            self.update_columns()

    def update_columns(self) -> None:
        self.grid_columnconfigure(len(self.cells), weight=0)
        self.update_idletasks()
