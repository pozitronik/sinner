import threading
from tkinter import filedialog, Entry, LEFT, Button, Label, END, Frame, BOTH, RIGHT, StringVar, W, EW, E, NE, NW

import cv2

from PIL import Image, ImageTk
from PIL.Image import Resampling
from customtkinter import CTkLabel, CTk, CTkSlider

from sinner.core import Core
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.utilities import is_image, is_video


class Preview:
    core: Core
    root: CTk
    preview_label: CTkLabel
    preview_slider: CTkSlider

    def __init__(self, core: Core):
        self.core = core
        self.root = CTk()
        self.root.title('Preview')
        self.root.protocol('WM_DELETE_WINDOW', lambda: self.destroy())
        self.root.resizable(width=True, height=True)
        self.current_position = StringVar()

    def show(self) -> CTk:
        self.init_preview()
        self.init_slider()
        self.init_open_source_control()
        self.init_open_target_control()
        self.update_preview(self.preview_label, int(self.preview_slider.get()))
        return self.root

    def init_preview(self) -> None:
        self.preview_label = CTkLabel(self.root, text='')

        # self.preview_label.bind('<Configure>', lambda event: self.resize_image(event, self.preview_label))

        self.preview_label.bind("<Double-Button-1>", lambda event: self.update_preview(self.preview_label, int(self.preview_slider.get()), True))
        self.preview_label.bind("<Button-2>", lambda event: self.change_source(int(self.preview_slider.get())))
        self.preview_label.bind("<Button-3>", lambda event: self.change_target(int(self.preview_slider.get())))
        self.preview_label.pack(fill='both', expand=True)

    def init_slider(self) -> None:
        frame = Frame(self.root, borderwidth=2)
        self.preview_slider = CTkSlider(frame, to=0, command=lambda frame_value: self.update_preview(self.preview_label, frame_value))
        if is_image(self.core.params.target_path):
            self.preview_slider.pack_forget()
        if is_video(self.core.params.target_path):
            video_frame_total = BaseFrameHandler.create(handler_name=self.core.params.frame_handler, target_path=self.core.params.target_path).fc
            self.preview_slider.configure(to=video_frame_total)
            self.preview_slider.pack(anchor=NW, side=LEFT, expand=True, fill=BOTH)
            self.preview_slider.set(video_frame_total / 2)

        current_position_label = Label(frame, textvariable=self.current_position)
        current_position_label.pack(anchor=NE, side=LEFT)
        preview_button = Button(frame, text="preview", compound=LEFT, command=lambda: self.update_preview(self.preview_label, int(self.preview_slider.get()), True))
        preview_button.pack(anchor=NE, side=LEFT)
        run_button = Button(frame, text="run", compound=LEFT, command=lambda: self.run_processing())
        run_button.pack(anchor=NE, side=LEFT)
        frame.pack(fill='x')

    def init_open_source_control(self) -> None:
        frame = Frame(self.root, borderwidth=2)
        path_entry = Entry(frame)
        path_entry.insert(END, self.core.params.source_path)
        path_entry.pack(side=LEFT, expand=True, fill=BOTH)

        open_button = Button(frame, text="Browse for source", width=20, command=lambda: self.change_source(int(self.preview_slider.get())))
        open_button.pack(side=RIGHT)
        frame.pack(fill='x')

    def init_open_target_control(self) -> None:
        frame = Frame(self.root, borderwidth=2)

        path_entry = Entry(frame)
        path_entry.insert(END, self.core.params.target_path)
        path_entry.pack(side=LEFT, expand=True, fill=BOTH)

        open_button = Button(frame, text="Browse for target", width=20, command=lambda: self.change_target(int(self.preview_slider.get())))
        open_button.pack(side=LEFT)
        frame.pack(fill='x')

    def change_source(self, frame_number: int = 0) -> None:
        if self.core.change_source(filedialog.askopenfilename(title='Select a source')):
            self.update_preview(self.preview_label, frame_number, True)

    def change_target(self, frame_number: int = 0) -> None:
        if self.core.change_target(filedialog.askopenfilename(title='Select a target')):
            self.update_preview(self.preview_label, frame_number, True)
            self.init_slider()

    @staticmethod
    def render_image_preview(frame: Frame) -> ImageTk.PhotoImage:
        image = Image.fromarray(frame)
        return ImageTk.PhotoImage(image)

    def update_preview(self, preview_label: CTkLabel, frame_number: int = 0, processed: bool = False) -> None:
        frame = self.core.get_frame(frame_number, processed)
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        image = ImageTk.PhotoImage(pil_image)
        preview_label.configure(image=image)
        preview_label.image = image
        self.current_position.set(f'{int(frame_number)}/{self.preview_slider.cget("to")}')

    @staticmethod
    def destroy():
        quit()

    @staticmethod
    def resize_image(event, label: CTkLabel):
        # Get the new size of the label
        pil_image = ImageTk.getimage(label.image)

        original_width, original_height = pil_image.size
        target_width, target_height = (event.width, event.height)

        if original_width / original_height > target_width / target_height:
            new_width = target_width
            new_height = int(original_height * (target_width / original_width))
        else:
            new_height = target_height
            new_width = int(original_width * (target_height / original_height))

        # Resize the image to fit the label
        resized_image = pil_image.resize((new_width, new_height), Resampling.LANCZOS)
        resized_photo_image = ImageTk.PhotoImage(resized_image)
        # Update the label's image
        label.configure(image=resized_photo_image)
        label.image = resized_photo_image

    def run_processing(self):
        thread = threading.Thread(target=self.core.run)
        thread.start()


