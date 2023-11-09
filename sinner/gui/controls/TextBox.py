from tkinter import Entry, NORMAL, END


class TextBox(Entry):

    def update_text(self, text: str | None) -> None:
        previous_state = self.cget("state")
        self.configure(state=NORMAL)
        self.delete(0, END)
        if text:
            self.insert(END, text)
        self.configure(state=previous_state)

    # schedule the update to avoid multithreading issues
    def set_text(self, text: str | None) -> None:
        self.master.after(0, self.update_text, text)
