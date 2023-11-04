from tkinter import Frame, Listbox, Entry, Button, END, SINGLE, LEFT, BOTH, Scrollbar, VERTICAL, Y, RIGHT


class StringListEditor(Frame):
    def __init__(self, master=None, predefined_list=None):
        super().__init__(master)
        self.master = master
        self.predefined_list = predefined_list if predefined_list else []
        self.string_list = []
        self.pack()

        # Create a Listbox for displaying and reordering items
        self.listbox = Listbox(self, selectmode=SINGLE, exportselection=0)
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.listbox.bind("<Button-1>", self.on_select)

        # Create a scrollbar for the Listbox
        scrollbar = Scrollbar(self, orient=VERTICAL)
        scrollbar.pack(side=LEFT, fill=Y)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Create a Frame to hold buttons and entry for adding/editing items
        self.button_frame = Frame(self)
        self.button_frame.pack(side=RIGHT, fill=Y)

        self.add_button = Button(self.button_frame, text="Add", command=self.add_item)
        self.add_button.pack()

        self.edit_button = Button(self.button_frame, text="Edit", command=self.edit_item)
        self.edit_button.pack()

        self.remove_button = Button(self.button_frame, text="Remove", command=self.remove_item)
        self.remove_button.pack()

        self.entry = Entry(self.button_frame)
        self.entry.pack()

        # Initialize the Listbox with predefined items
        for item in self.predefined_list:
            self.listbox.insert(END, item)
        self.update_string_list()

    def add_item(self):
        new_item = self.entry.get()
        if new_item:
            self.listbox.insert(END, new_item)
            self.entry.delete(0, END)
            self.update_string_list()

    def edit_item(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_index = selected_index[0]
            edited_item = self.entry.get()
            if edited_item:
                self.listbox.delete(selected_index)
                self.listbox.insert(selected_index, edited_item)
                self.entry.delete(0, END)
                self.update_string_list()

    def remove_item(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            self.listbox.delete(selected_index)
            self.update_string_list()

    def on_select(self, event):
        self.entry.delete(0, END)
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_item = self.listbox.get(selected_index)
            self.entry.insert(0, selected_item)

    def update_string_list(self):
        self.string_list = [self.listbox.get(index) for index in range(self.listbox.size())]

