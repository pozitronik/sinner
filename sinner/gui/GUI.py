import os.path
import threading
from tkinter import filedialog, Entry, LEFT, Button, Label, END, Frame, BOTH, RIGHT, StringVar, NE, NW, X, DISABLED, NORMAL, Event, Canvas, CENTER, BOTTOM, Y, NSEW
from tkinter.ttk import Progressbar
from typing import List, Tuple

import PIL
import cv2

from PIL import Image, ImageTk
from PIL.ImageTk import PhotoImage
from customtkinter import CTk, CTkSlider

from sinner import typing
from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.Status import Status
from sinner.gui.GUIProcessingCore import GUIProcessingCore
from sinner.gui.ImageList import ImageList, FrameThumbnail
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.utilities import is_image, is_video, is_int
from sinner.validators.AttributeLoader import Rules


class GUI(Status):
    # class attributes
    processing_core: GUIProcessingCore
    run_thread: threading.Thread | None

    source_path: str = ''
    target_path: str = ''
    preview_max_width: float
    preview_max_height: float
    _extractor_handler: BaseFrameHandler | None = None
    _previews: dict[int, List[Tuple[typing.Frame, str]]] = {}  # position: [frame, caption]
    _current_frame: typing.Frame

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
            {
                'module_help': 'GUI module'
            }
        ]

    def __init__(self, core: GUIProcessingCore):
        self.processing_core = core
        super().__init__(self.processing_core.parameters)
        self.run_thread = None

        #  window controls
        self.PreviewWindow: CTk = CTk()
        self.PreviewCanvas: Canvas = Canvas(self.PreviewWindow)
        self.PreviewFrames: ImageList = ImageList(parent=self.PreviewWindow)
        self.NavigateSliderFrame: Frame = Frame(self.PreviewWindow, borderwidth=2)
        self.NavigateSlider: CTkSlider = CTkSlider(self.NavigateSliderFrame, to=0)
        self.NavigatePositionLabel: Label = Label(self.NavigateSliderFrame)
        self.PreviewButton: Button = Button(self.NavigateSliderFrame, text="Preview", compound=LEFT)
        self.SaveButton: Button = Button(self.NavigateSliderFrame, text="save", compound=LEFT)
        self.SourcePathFrame: Frame = Frame(self.PreviewWindow, borderwidth=2)
        self.SourcePathEntry: Entry = Entry(self.SourcePathFrame)
        self.SelectSourceDialog = filedialog
        self.ChangeSourceButton: Button = Button(self.SourcePathFrame, text="Browse for source", width=20)
        self.TargetPathFrame: Frame = Frame(self.PreviewWindow, borderwidth=2)
        self.TargetPathEntry: Entry = Entry(self.TargetPathFrame)
        self.SelectTargetDialog = filedialog
        self.ChangeTargetButton: Button = Button(self.TargetPathFrame, text="Browse for target", width=20)
        self.ProgressBarFrame: Frame = Frame(self.PreviewWindow, borderwidth=2)
        self.ProgressBar: Progressbar = Progressbar(self.ProgressBarFrame, mode='indeterminate')

        self.PreviewWindow.title('😈sinner')
        self.PreviewWindow.protocol('WM_DELETE_WINDOW', lambda: self.destroy())
        self.PreviewWindow.resizable(width=True, height=True)
        self.PreviewWindow.bind("<KeyRelease>", lambda event: self.key_release(event))
        self.PreviewWindow.bind("<KeyPress>", lambda event: self.key_press(event))
        # class attributes
        self.current_position: StringVar = StringVar()

        # init gui
        self.PreviewCanvas.bind("<Double-Button-1>", lambda event: self.update_preview(int(self.NavigateSlider.get()), True))
        self.PreviewCanvas.bind("<Button-2>", lambda event: self.change_source(int(self.NavigateSlider.get())))
        self.PreviewCanvas.bind("<Button-3>", lambda event: self.change_target())
        self.PreviewCanvas.bind("<Configure>", lambda event: self.resize_preview(event))
        # init generated frames list
        self.PreviewCanvas.pack(fill=BOTH, expand=True)
        self.PreviewFrames.pack(fill=X, expand=False, anchor=NW)
        # init slider
        self.NavigateSlider.configure(command=lambda frame_value: self.update_preview(int(frame_value)))
        self.update_slider()
        self.NavigatePositionLabel.configure(textvariable=self.current_position)
        self.NavigatePositionLabel.pack(anchor=NE, side=LEFT)
        self.PreviewButton.configure(command=lambda: self.update_preview(int(self.NavigateSlider.get()), True))
        self.PreviewButton.pack(anchor=NE, side=LEFT)
        self.SaveButton.configure(command=lambda: self.save_frame())
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
            self.processing_core.parameters.source = self.source_path
            self.processing_core.load(self.processing_core.parameters)
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
            self.processing_core.parameters.target = self.target_path
            self.processing_core.load(self.processing_core.parameters)
            self._extractor_handler = None
            self.update_preview(self.update_slider(), True)
            self.TargetPathEntry.configure(state=NORMAL)
            self.TargetPathEntry.delete(0, END)
            self.TargetPathEntry.insert(END, self.target_path)
            self.TargetPathEntry.configure(state=DISABLED)
            self._previews.clear()

    def get_frames(self, frame_number: int = 0, processed: bool = False) -> List[Tuple[typing.Frame, str]]:
        saved_frames = self._previews.get(frame_number)
        if not saved_frames and processed:
            self._previews[frame_number] = self.processing_core.get_frame(frame_number, self.frame_handler, processed)
        return [saved_frames[0]] if saved_frames else self.processing_core.get_frame(frame_number, self.frame_handler, processed)

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

    def show_image(self, image: PhotoImage | None) -> None:
        self.PreviewCanvas.create_image(self.PreviewCanvas.winfo_width() // 2, self.PreviewCanvas.winfo_height() // 2, image=image)
        self.PreviewCanvas.photo = image  # type: ignore[attr-defined]

    def resize_preview(self, event: Event) -> None:
        image = Image.fromarray(cv2.cvtColor(self._current_frame, cv2.COLOR_BGR2RGB))
        image = self.resize_image(image, (event.width, event.height))
        self.show_image(ImageTk.PhotoImage(image))

    @staticmethod
    def resize_image(image: PIL.Image, size: tuple[int, int]) -> Image:
        aspect_ratio = image.size[0] / image.size[1]
        new_width = size[0]
        new_height = int(size[0] / aspect_ratio)
        if new_height > size[1]:
            new_height = size[1]
            new_width = int(size[1] * aspect_ratio)

        resized_image = image.resize((new_width, new_height)) if new_width > 0 and new_height > 0 else image

        return resized_image

    def show_frame(self, frame: typing.Frame | None = None) -> None:
        self._current_frame = frame
        if frame is None:
            self.show_image(None)
        else:
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            image = self.resize_image(image, (self.PreviewCanvas.winfo_width(), self.PreviewCanvas.winfo_height()))
            self.show_image(ImageTk.PhotoImage(image))

    @staticmethod
    def destroy() -> None:
        quit()

    def update_progress(self, value: int) -> None:
        self.ProgressBar['value'] = value

    def save_frame(self) -> None:
        save_file = filedialog.asksaveasfilename(title='Save frame', defaultextension='png')
        if save_file != ' ':
            ImageTk.getimage(self._tmp_image).save(save_file)

    @property
    def frame_handler(self) -> BaseFrameHandler:
        if self._extractor_handler is None:
            self._extractor_handler = BatchProcessingCore.suggest_handler(self.target_path, self.processing_core.parameters)
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
