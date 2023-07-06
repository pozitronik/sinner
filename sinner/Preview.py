import os.path
import threading
from tkinter import filedialog, Entry, LEFT, Button, Label, END, Frame, BOTH, RIGHT, StringVar, NE, NW, X
from tkinter.ttk import Progressbar

import cv2

from PIL import Image, ImageTk
from customtkinter import CTkLabel, CTk, CTkSlider

from sinner.core import Core
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.utilities import is_image, is_video


class Preview:
    core: Core
    root: CTk
    source_path_entry: Entry
    target_path_entry: Entry
    preview_label: CTkLabel
    preview_slider: CTkSlider
    progress_bar: Progressbar
    run_thread: threading.Thread | None

    def __init__(self, core: Core):
        self.run_thread = None
        self.core = core
        self.root = CTk()
        self.root.title('Preview')
        self.root.protocol('WM_DELETE_WINDOW', lambda: self.destroy())
        self.root.resizable(width=True, height=True)
        self.current_position = StringVar()

    def show(self) -> CTk:
        self.init_preview()
        self.init_slider()
        # self.init_progressbar(maximum=int(self.preview_slider.cget('to')))
        self.init_open_source_control()
        self.init_open_target_control()
        self.update_preview(self.preview_label, int(self.preview_slider.get()))
        return self.root

    def init_preview(self) -> None:
        self.preview_label = CTkLabel(self.root, text='')

        self.preview_label.bind("<Double-Button-1>", lambda event: self.update_preview(self.preview_label, int(self.preview_slider.get()), True))
        self.preview_label.bind("<Button-2>", lambda event: self.change_source(int(self.preview_slider.get())))
        self.preview_label.bind("<Button-3>", lambda event: self.change_target())
        self.preview_label.pack(fill='both', expand=True)

    def init_slider(self) -> None:
        frame = Frame(self.root, borderwidth=2)
        self.preview_slider = CTkSlider(frame, to=0, command=lambda frame_value: self.update_preview(self.preview_label, int(frame_value)))
        self.update_slider()

        current_position_label = Label(frame, textvariable=self.current_position)
        current_position_label.pack(anchor=NE, side=LEFT)
        preview_button = Button(frame, text="preview", compound=LEFT, command=lambda: self.update_preview(self.preview_label, int(self.preview_slider.get()), True))
        preview_button.pack(anchor=NE, side=LEFT)
        save_button = Button(frame, text="save", compound=LEFT, command=lambda: self.save_frame(self.preview_label))
        save_button.pack(anchor=NE, side=LEFT)
        # run_button = Button(frame, text="run", compound=LEFT, command=lambda: self.run_processing())
        # run_button.pack(anchor=NE, side=LEFT)
        frame.pack(fill=X)

    def update_slider(self) -> int:
        if is_image(self.core.params.target_path):
            self.preview_slider.pack_forget()
        if is_video(self.core.params.target_path):
            video_frame_total = BaseFrameHandler.create(handler_name=self.core.params.frame_handler, target_path=self.core.params.target_path).fc
            self.preview_slider.configure(to=video_frame_total)
            self.preview_slider.pack(anchor=NW, side=LEFT, expand=True, fill=BOTH)
            self.preview_slider.set(video_frame_total / 2)
        return int(self.preview_slider.get())

    def init_open_source_control(self) -> None:
        frame = Frame(self.root, borderwidth=2)
        self.source_path_entry = Entry(frame)
        self.source_path_entry.insert(END, self.core.params.source_path)
        self.source_path_entry.pack(side=LEFT, expand=True, fill=BOTH)

        open_button = Button(frame, text="Browse for source", width=20, command=lambda: self.change_source(int(self.preview_slider.get())))
        open_button.pack(side=RIGHT)
        frame.pack(fill=X)

    def init_open_target_control(self) -> None:
        frame = Frame(self.root, borderwidth=2)

        self.target_path_entry = Entry(frame)
        self.target_path_entry.insert(END, self.core.params.target_path)
        self.target_path_entry.pack(side=LEFT, expand=True, fill=BOTH)

        open_button = Button(frame, text="Browse for target", width=20, command=lambda: self.change_target())
        open_button.pack(side=LEFT)
        frame.pack(fill=X)

    def change_source(self, frame_number: int = 0) -> None:
        if self.core.change_source(filedialog.askopenfilename(title='Select a source', initialdir=os.path.dirname(self.core.params.source_path))):
            self.update_preview(self.preview_label, frame_number, True)
            self.source_path_entry.delete(0, END)
            self.source_path_entry.insert(END, self.core.params.source_path)

    def change_target(self) -> None:

        if self.core.change_target(filedialog.askopenfilename(title='Select a target', initialdir=os.path.dirname(self.core.params.target_path))):
            self.update_preview(self.preview_label, self.update_slider(), True)
            self.target_path_entry.delete(0, END)
            self.target_path_entry.insert(END, self.core.params.target_path)

    @staticmethod
    def render_image_preview(frame: Frame) -> ImageTk.PhotoImage:
        image = Image.fromarray(frame)
        return ImageTk.PhotoImage(image)

    def update_preview(self, preview_label: CTkLabel, frame_number: int = 0, processed: bool = False) -> None:
        frame = self.core.get_frame(frame_number, processed)
        if frame is not None:
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            image = ImageTk.PhotoImage(pil_image)
            preview_label.configure(image=image)
            preview_label.image = image
        self.current_position.set(f'{int(frame_number)}/{self.preview_slider.cget("to")}')

    @staticmethod
    def destroy() -> None:
        quit()

    def run_processing(self) -> None:
        if self.run_thread is None:
            self.run_thread = threading.Thread(target=self.core.run, args=(self.update_progress,))
            self.run_thread.start()
        else:
            self.core.stop()
            self.run_thread.join()

    def update_progress(self, value: int) -> None:
        self.progress_bar['value'] = value

    def init_progressbar(self, value: int = 0, maximum: int = 0) -> None:
        frame = Frame(self.root, borderwidth=2)
        self.progress_bar = Progressbar(frame, mode='indeterminate', value=value, maximum=maximum)
        self.progress_bar.pack(pady=10, fill=X)
        frame.pack(fill=X)

    @staticmethod
    def save_frame(preview_label: CTkLabel):
        save_file = filedialog.asksaveasfilename(title='Save frame', defaultextension='png')
        if save_file != ' ':
            tk_image: ImageTk.PhotoImage = preview_label.cget('image')
            pil_image = ImageTk.getimage(tk_image)
            pil_image.save(save_file)
