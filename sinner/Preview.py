import os.path
import threading
from tkinter import filedialog, Entry, LEFT, Button, Label, END, Frame, BOTH, RIGHT, StringVar, NE, NW, X
from tkinter.ttk import Progressbar

import cv2

from PIL import Image, ImageTk
from PIL.ImageTk import PhotoImage
from customtkinter import CTkLabel, CTk, CTkSlider

from sinner.core import Core
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.utilities import is_image, is_video


class Preview:
    #  window controls
    PreviewWindow: CTk
    SourcePathEntry: Entry
    TargetPathEntry: Entry
    PreviewFrameLabel: CTkLabel
    NavigateSliderFrame: Frame
    NavigateSlider: CTkSlider
    ProgressBar: Progressbar
    SourcePathFrame: Frame
    TargetPathFrame: Frame
    ProgressBarFrame: Frame

    # class attributes
    core: Core
    run_thread: threading.Thread | None

    def __init__(self, core: Core):
        self.run_thread = None
        self.core = core
        self.PreviewWindow = CTk()
        self.PreviewWindow.title('Preview')
        self.PreviewWindow.protocol('WM_DELETE_WINDOW', lambda: self.destroy())
        self.PreviewWindow.resizable(width=True, height=True)
        self.current_position = StringVar()

    def show(self) -> CTk:
        self.init_preview()
        self.init_slider()
        # self.init_progressbar(maximum=int(self.NavigateSlider.cget('to')))
        self.init_open_source_control()
        self.init_open_target_control()
        self.update_preview(self.PreviewFrameLabel, int(self.NavigateSlider.get()))
        return self.PreviewWindow

    def init_preview(self) -> None:
        self.PreviewFrameLabel = CTkLabel(self.PreviewWindow, text='')

        self.PreviewFrameLabel.bind("<Double-Button-1>", lambda event: self.update_preview(self.PreviewFrameLabel, int(self.NavigateSlider.get()), True))
        self.PreviewFrameLabel.bind("<Button-2>", lambda event: self.change_source(int(self.NavigateSlider.get())))
        self.PreviewFrameLabel.bind("<Button-3>", lambda event: self.change_target())
        self.PreviewFrameLabel.pack(fill='both', expand=True)

    def init_slider(self) -> None:
        self.NavigateSliderFrame = Frame(self.PreviewWindow, borderwidth=2)
        self.NavigateSlider = CTkSlider(self.NavigateSliderFrame, to=0, command=lambda frame_value: self.update_preview(self.PreviewFrameLabel, int(frame_value)))
        self.update_slider()

        current_position_label = Label(self.NavigateSliderFrame, textvariable=self.current_position)
        current_position_label.pack(anchor=NE, side=LEFT)
        preview_button = Button(self.NavigateSliderFrame, text="preview", compound=LEFT, command=lambda: self.update_preview(self.PreviewFrameLabel, int(self.NavigateSlider.get()), True))
        preview_button.pack(anchor=NE, side=LEFT)
        save_button = Button(self.NavigateSliderFrame, text="save", compound=LEFT, command=lambda: self.save_frame(self.PreviewFrameLabel))
        save_button.pack(anchor=NE, side=LEFT)
        # run_button = Button(self.NavigateSliderFrame, text="run", compound=LEFT, command=lambda: self.run_processing())
        # run_button.pack(anchor=NE, side=LEFT)
        self.NavigateSliderFrame.pack(fill=X)

    def update_slider(self) -> int:
        if is_image(self.core.params.target_path):
            self.NavigateSlider.pack_forget()
        if is_video(self.core.params.target_path):
            video_frame_total = BaseFrameHandler.create(handler_name=self.core.params.frame_handler, target_path=self.core.params.target_path).fc
            self.NavigateSlider.configure(to=video_frame_total)
            self.NavigateSlider.pack(anchor=NW, side=LEFT, expand=True, fill=BOTH)
            self.NavigateSlider.set(video_frame_total / 2)
        return int(self.NavigateSlider.get())

    def init_open_source_control(self) -> None:
        self.SourcePathFrame = Frame(self.PreviewWindow, borderwidth=2)
        self.SourcePathEntry = Entry(self.SourcePathFrame)
        self.SourcePathEntry.insert(END, self.core.params.source_path)
        self.SourcePathEntry.pack(side=LEFT, expand=True, fill=BOTH)

        open_button = Button(self.SourcePathFrame, text="Browse for source", width=20, command=lambda: self.change_source(int(self.NavigateSlider.get())))
        open_button.pack(side=RIGHT)
        self.SourcePathFrame.pack(fill=X)

    def init_open_target_control(self) -> None:
        self.TargetPathFrame = Frame(self.PreviewWindow, borderwidth=2)

        self.TargetPathEntry = Entry(self.TargetPathFrame)
        self.TargetPathEntry.insert(END, self.core.params.target_path)
        self.TargetPathEntry.pack(side=LEFT, expand=True, fill=BOTH)

        open_button = Button(self.TargetPathFrame, text="Browse for target", width=20, command=lambda: self.change_target())
        open_button.pack(side=LEFT)
        self.TargetPathFrame.pack(fill=X)

    def change_source(self, frame_number: int = 0) -> None:
        if self.core.change_source(filedialog.askopenfilename(title='Select a source', initialdir=os.path.dirname(self.core.params.source_path))):
            self.update_preview(self.PreviewFrameLabel, frame_number, True)
            self.SourcePathEntry.delete(0, END)
            self.SourcePathEntry.insert(END, self.core.params.source_path)

    def change_target(self) -> None:

        if self.core.change_target(filedialog.askopenfilename(title='Select a target', initialdir=os.path.dirname(self.core.params.target_path))):
            self.update_preview(self.PreviewFrameLabel, self.update_slider(), True)
            self.TargetPathEntry.delete(0, END)
            self.TargetPathEntry.insert(END, self.core.params.target_path)

    @staticmethod
    def render_image_preview(frame: Frame) -> PhotoImage:
        return PhotoImage(Image.fromarray(frame))

    def update_preview(self, preview_label: CTkLabel, frame_number: int = 0, processed: bool = False) -> None:
        frame = self.core.get_frame(frame_number, processed)
        if frame is not None:
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            image = PhotoImage(pil_image)
            preview_label.configure(image=image)
            preview_label.image = image
        self.current_position.set(f'{int(frame_number)}/{self.NavigateSlider.cget("to")}')

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
        self.ProgressBar['value'] = value

    def init_progressbar(self, value: int = 0, maximum: int = 0) -> None:
        self.ProgressBarFrame = Frame(self.PreviewWindow, borderwidth=2)
        self.ProgressBar = Progressbar(self.ProgressBarFrame, mode='indeterminate', value=value, maximum=maximum)
        self.ProgressBar.pack(pady=10, fill=X)
        self.ProgressBarFrame.pack(fill=X)

    @staticmethod
    def save_frame(preview_label: CTkLabel):
        save_file = filedialog.asksaveasfilename(title='Save frame', defaultextension='png')
        if save_file != ' ':
            tk_image: ImageTk.PhotoImage = preview_label.cget('image')
            pil_image = ImageTk.getimage(tk_image)
            pil_image.save(save_file)
