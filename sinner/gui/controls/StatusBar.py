from tkinter import Frame, BOTTOM, Misc, X
from typing import Dict

from sinner.gui.controls.TextBox import TextBox
from sinner.gui.controls.Tooltip import Tooltip


class StatusBar(Frame):
    cells: Dict[str, TextBox]

    def __init__(self, master: Misc | None, cells: Dict[str, str] | None = None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(side=BOTTOM, expand=True, fill=X)

        if cells is not None:  # there's initial items
            self.grid_columnconfigure(len(cells))
            for name, value in cells.items():
                self.create_cell(name, value)
        else:
            self.cells = {}

    def item(self, name: str, value: str, span: int = 1) -> TextBox:
        if name in self.cells:
            cell = self.cells[name]
            if value is not None:
                cell.set_text(value)
        else:
            cell = self.create_cell(name, value, span)
        return cell

    def create_cell(self, name: str, value: str, span: int = 1) -> TextBox:
        self.grid_columnconfigure(len(self.cells), weight=1)
        cell = TextBox(self, state="readonly")
        cell.grid(row=0, column=len(self.cells), columnspan=span, sticky="ew")
        cell.set_text(value)
        self.cells[name] = cell
        tooltip = Tooltip(cell, text=name)
        return cell

    def remove_item(self, name: str) -> None:
        if name in self.cells:
            cell = self.cells.pop(name)
            cell.destroy()
            self.update_columns()

    def update_columns(self) -> None:
        self.grid_columnconfigure(len(self.cells), weight=0)
        self.update_idletasks()
