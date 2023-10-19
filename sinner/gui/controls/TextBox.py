from tkinter import Entry, NORMAL, END

READONLY = "readonly"


class TextBox(Entry):

    def set_text(self, text: str) -> None:
        previous_state = self.cget("state")
        self.configure(state=NORMAL)
        self.delete(0, END)
        self.insert(END, text)
        self.configure(state=previous_state)
