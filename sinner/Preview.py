import os.path
import threading
from tkinter import filedialog, Entry, LEFT, Button, Label, END, Frame, BOTH, RIGHT, StringVar, NE, NW, X, DISABLED, NORMAL, Event
from tkinter.ttk import Progressbar
from typing import List, Tuple

import cv2

from PIL import Image, ImageTk
from PIL.ImageTk import PhotoImage
from customtkinter import CTkLabel, CTk, CTkSlider

from sinner import typing
from sinner.Core import Core
from sinner.Status import Status, Mood
from sinner.gui.ImageList import ImageList, FrameThumbnail
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.utilities import is_image, is_video, is_int
from sinner.validators.AttributeLoader import Rules, AttributeLoader


class Preview(AttributeLoader, Status):
    #  window controls
    PreviewWindow: CTk = CTk()
    PreviewFrame: Frame = Frame(PreviewWindow, borderwidth=2)
    PreviewFrameLabel: CTkLabel = CTkLabel(PreviewWindow, text='')
    PreviewFrames: ImageList = ImageList(parent=PreviewWindow)

    NavigateSliderFrame: Frame = Frame(PreviewWindow, borderwidth=2)
    NavigateSlider: CTkSlider = CTkSlider(NavigateSliderFrame, to=0)
    NavigatePositionLabel: Label = Label(NavigateSliderFrame)
    PreviewButton: Button = Button(NavigateSliderFrame, text="Preview", compound=LEFT)
    SaveButton: Button = Button(NavigateSliderFrame, text="save", compound=LEFT)
    SourcePathFrame: Frame = Frame(PreviewWindow, borderwidth=2)
    SourcePathEntry: Entry = Entry(SourcePathFrame)
    SelectSourceDialog = filedialog
    ChangeSourceButton: Button = Button(SourcePathFrame, text="Browse for source", width=20)
    TargetPathFrame: Frame = Frame(PreviewWindow, borderwidth=2)
    TargetPathEntry: Entry = Entry(TargetPathFrame)
    SelectTargetDialog = filedialog
    ChangeTargetButton: Button = Button(TargetPathFrame, text="Browse for target", width=20)
    ProgressBarFrame: Frame = Frame(PreviewWindow, borderwidth=2)
    ProgressBar: Progressbar = Progressbar(ProgressBarFrame, mode='indeterminate')

    # class attributes
    core: Core
    run_thread: threading.Thread | None
    current_position: StringVar = StringVar()
    source_path: str = ''
    target_path: str = ''
    preview_max_width: float
    preview_max_height: float
    _extractor_handler: BaseFrameHandler | None = None
    _previews: dict[int, List[Tuple[typing.Frame, str]]] = {}  # position: [frame, caption]

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path'
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path'
            },
            {
                'parameter': {'preview-max-height', 'preview-height-max'},
                'attribute': 'preview_max_height',
                'default': None,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Maximum preview window height'
            },
            {
                'parameter': {'preview-max-width', 'preview-width-max'},
                'attribute': 'preview_max_width',
                'default': None,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Maximum preview window width'
            },
        ]

    def __init__(self, core: Core):
        self.core = core
        super().__init__(self.core.parameters)
        self.run_thread = None
        self.PreviewWindow.title('😈sinner')
        self.PreviewWindow.protocol('WM_DELETE_WINDOW', lambda: self.destroy())
        self.PreviewWindow.resizable(width=True, height=True)
        self.PreviewWindow.bind("<KeyRelease>", lambda event: self.key_release(event))
        self.PreviewWindow.bind("<KeyPress>", lambda event: self.key_press(event))
        # init gui
        self.PreviewFrameLabel.bind("<Double-Button-1>", lambda event: self.update_preview(int(self.NavigateSlider.get()), True))
        self.PreviewFrameLabel.bind("<Button-2>", lambda event: self.change_source(int(self.NavigateSlider.get())))
        self.PreviewFrameLabel.bind("<Button-3>", lambda event: self.change_target())
        self.PreviewFrameLabel.pack(fill='both', expand=True)
        # init generated frames list
        self.PreviewFrames.pack(fill='both', expand=True)
        # init slider
        self.NavigateSlider.configure(command=lambda frame_value: self.update_preview(int(frame_value)))
        self.update_slider()
        self.NavigatePositionLabel.configure(textvariable=self.current_position)
        self.NavigatePositionLabel.pack(anchor=NE, side=LEFT)
        self.PreviewButton.configure(command=lambda: self.update_preview(int(self.NavigateSlider.get()), True))
        self.PreviewButton.pack(anchor=NE, side=LEFT)
        self.SaveButton.configure(command=lambda: self.save_frame(self.PreviewFrameLabel))
        self.SaveButton.pack(anchor=NE, side=LEFT)
        self.NavigateSliderFrame.pack(fill=X)
        # init source selection control set
        self.SourcePathEntry.insert(END, self.source_path)
        self.SourcePathEntry.configure(state=DISABLED)
        self.SourcePathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeSourceButton.configure(command=lambda: self.change_source(int(self.NavigateSlider.get())))
        self.ChangeSourceButton.pack(side=RIGHT)
        self.SourcePathFrame.pack(fill=X)
        # init target selection control set
        self.TargetPathEntry.insert(END, self.target_path)
        self.TargetPathEntry.configure(state=DISABLED)
        self.TargetPathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeTargetButton.configure(command=lambda: self.change_target())
        self.ChangeTargetButton.pack(side=LEFT)
        self.TargetPathFrame.pack(fill=X)
        # init progress bar
        self.ProgressBar.pack(pady=10, fill=X)
        # self.ProgressBarFrame.pack(fill=X) # hide for now

    def show(self) -> CTk:
        self.update_preview(int(self.NavigateSlider.get()))
        return self.PreviewWindow

    def update_slider(self) -> int:
        if is_image(self.target_path):
            self.NavigateSlider.configure(to=1)
            self.NavigateSlider.set(1)
            self.NavigateSlider.pack_forget()
        if is_video(self.target_path):
            video_frame_total = 1
            if self.frame_handler is not None:
                video_frame_total = self.frame_handler.fc
            self.NavigateSlider.configure(to=video_frame_total)
            self.NavigateSlider.pack(anchor=NW, side=LEFT, expand=True, fill=BOTH)
            self.NavigateSlider.set(video_frame_total / 2)
        self.current_position.set(f'{int(self.NavigateSlider.get())}/{self.NavigateSlider.cget("to")}')  # todo
        return int(self.NavigateSlider.get())

    def change_source(self, frame_number: int = 0) -> None:
        path = self.SelectSourceDialog.askopenfilename(title='Select a source', initialdir=os.path.dirname(self.source_path))
        if path != '':
            self.source_path = path
            self.core.parameters.source = self.source_path
            self.core.load(self.core.parameters)
            self._previews.clear()
            self.update_preview(frame_number, True)
            self.SourcePathEntry.configure(state=NORMAL)
            self.SourcePathEntry.delete(0, END)
            self.SourcePathEntry.insert(END, self.source_path)
            self.SourcePathEntry.configure(state=DISABLED)

    def change_target(self) -> None:
        path = self.SelectTargetDialog.askopenfilename(title='Select a target', initialdir=os.path.dirname(self.target_path))
        if path != '':
            self._previews.clear()
            self.target_path = path
            self.core.parameters.target = self.target_path
            self.core.load(self.core.parameters)
            self._extractor_handler = None
            self.update_preview(self.update_slider(), True)
            self.TargetPathEntry.configure(state=NORMAL)
            self.TargetPathEntry.delete(0, END)
            self.TargetPathEntry.insert(END, self.target_path)
            self.TargetPathEntry.configure(state=DISABLED)
            self._previews.clear()

    @staticmethod
    def render_image_preview(frame: typing.Frame) -> PhotoImage:
        return PhotoImage(Image.fromarray(frame))

    def get_frames(self, frame_number: int = 0, processed: bool = False) -> List[Tuple[typing.Frame, str]]:
        saved_frames = self._previews.get(frame_number)
        if not saved_frames and processed:
            self._previews[frame_number] = self.core.get_frame(frame_number, self.frame_handler, processed)
        return [saved_frames[0]] if saved_frames else self.core.get_frame(frame_number, self.frame_handler, processed)

    def update_preview(self, frame_number: int = 0, processed: bool = False) -> None:
        frames = self.get_frames(frame_number, processed)
        if frames:
            if processed:
                self.PreviewFrames.show([FrameThumbnail(frame=frame[0], caption=frame[1], position=frame_number, onclick=self.show_saved) for frame in frames])
                self.show_frame(frames[-1][0])
            else:
                self.show_frame(frames[0][0])
        else:
            self.show_frame()
        self.current_position.set(f'{frame_number}/{self.NavigateSlider.cget("to")}')

    def show_saved(self, frame_number: int, thumbnail_index: int) -> None:
        frames = self._previews.get(frame_number)
        if frames:
            self.show_frame(frames[thumbnail_index][0])

    def resize_frame(self, frame: typing.Frame) -> typing.Frame:
        current_height, current_width = frame.shape[:2]
        if self.preview_max_height is not None and current_height > self.preview_max_height:
            scale = self.preview_max_height / current_height
            frame = cv2.resize(frame, (int(current_width * scale), int(current_height * scale)))
        if self.preview_max_width is not None and current_width > self.preview_max_width:
            scale = self.preview_max_width / current_width
            frame = cv2.resize(frame, (int(current_width * scale), int(current_height * scale)))
        return frame

    def show_frame(self, frame: typing.Frame | None = None) -> None:
        if frame is not None:
            frame = self.resize_frame(frame)
            image = PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))  # when replaced to CTkImage, it looks wrong
            self.PreviewFrameLabel.configure(image=image)
            self.PreviewFrameLabel.image = image
        else:
            self.PreviewFrameLabel.configure(image=None)
            self.PreviewFrameLabel.image = None

    @staticmethod
    def destroy() -> None:
        quit()

    def run_processing(self) -> None:
        if self.run_thread is None:
            self.ProgressBar.configure(value=0, maximum=int(self.NavigateSlider.cget('to')))
            self.run_thread = threading.Thread(target=self.core.run, args=(self.update_progress,))
            self.run_thread.start()
        else:
            self.core.stop()
            self.run_thread.join()

    def update_progress(self, value: int) -> None:
        self.ProgressBar['value'] = value

    @staticmethod
    def save_frame(preview_label: CTkLabel) -> None:
        save_file = filedialog.asksaveasfilename(title='Save frame', defaultextension='png')
        if save_file != ' ':
            ImageTk.getimage(preview_label.cget('image')).save(save_file)

    @property
    def frame_handler(self) -> BaseFrameHandler | None:
        if self._extractor_handler is None:
            try:
                self._extractor_handler = Core.suggest_handler(self.core.parameters, self.target_path)
            except Exception as exception:
                self.update_status(message=str(exception), mood=Mood.BAD)
        return self._extractor_handler

    def key_release(self, event: Event) -> None:  # type: ignore[type-arg]
        if event.keycode == 37 or event.keycode == 39:
            self.update_preview(int(self.NavigateSlider.get()))

    def key_press(self, event: Event) -> None:  # type: ignore[type-arg]
        if event.keycode == 37:
            self.NavigateSlider.set(max(1, int(self.NavigateSlider.get() - 1)))
        if event.keycode == 39:
            self.NavigateSlider.set(min(self.NavigateSlider.cget("to"), self.NavigateSlider.get() + 1))
        self.current_position.set(f'{int(self.NavigateSlider.get())}/{self.NavigateSlider.cget("to")}')
