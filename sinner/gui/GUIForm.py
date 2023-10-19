from argparse import Namespace
from tkinter import filedialog, Entry, LEFT, Button, Label, END, Frame, BOTH, RIGHT, StringVar, NE, NW, X, Event, NORMAL

from customtkinter import CTk

from sinner.Status import Status
from sinner.gui.GUIModel import GUIModel
from sinner.gui.controls.FrameThumbnail import FrameThumbnail
from sinner.gui.controls.ImageList import ImageList
from sinner.gui.controls.NavigateSlider import NavigateSlider
from sinner.gui.controls.PreviewCanvas import PreviewCanvas
from sinner.utilities import is_int, is_image, is_video
from sinner.validators.AttributeLoader import Rules


# GUI View
class GUIForm(Status):
    # class attributes
    GUIModel: GUIModel
    current_position: StringVar  # current position variable

    show_frames_widget: bool
    fw_height: int
    fw_width: int

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'show-frames-widget', 'frames-widget'},
                'attribute': 'show_frames_widget',
                'default': True,
                'help': 'Show processed frames widget'
            },
            {
                'parameter': {'frames-widget-width', 'fw-width'},
                'attribute': 'fw_width',
                'default': -1,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Processed widget maximum width, -1 to set as 10% of original image size'
            },
            {
                'parameter': {'frames-widget-height', 'fw-height'},
                'attribute': 'fw_height',
                'default': -1,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Processed widget maximum height, -1 to set as 10% of original image size'
            },
            {
                'module_help': 'GUI Form'
            }
        ]

    def __init__(self, parameters: Namespace):
        super().__init__(parameters)
        self.GUIModel = GUIModel(parameters)

        #  window controls
        self.PreviewWindow: CTk = CTk()  # the main window
        self.PreviewCanvas: PreviewCanvas = PreviewCanvas(self.PreviewWindow)  # the main preview
        self.PreviewFrames: ImageList = ImageList(parent=self.PreviewWindow, size=(self.fw_width, self.fw_height))  # the preview of processed frames
        self.NavigateSliderFrame: Frame = Frame(self.PreviewWindow, borderwidth=2)
        self.NavigateSlider: NavigateSlider = NavigateSlider(self.NavigateSliderFrame, to=0)
        self.NavigatePositionLabel: Label = Label(self.NavigateSliderFrame)
        # button controls
        self.RunButton: Button = Button(self.NavigateSliderFrame, text="PLAY", compound=LEFT)
        self.PreviewButton: Button = Button(self.NavigateSliderFrame, text="TEST", compound=LEFT)
        self.SaveButton: Button = Button(self.NavigateSliderFrame, text="SAVE", compound=LEFT)
        # source/target selection controls
        self.SourcePathFrame: Frame = Frame(self.PreviewWindow, borderwidth=2)
        self.SourcePathEntry: Entry = Entry(self.SourcePathFrame)
        self.SelectSourceDialog = filedialog
        self.ChangeSourceButton: Button = Button(self.SourcePathFrame, text="Browse for source", width=20)
        self.TargetPathFrame: Frame = Frame(self.PreviewWindow, borderwidth=2)
        self.TargetPathEntry: Entry = Entry(self.TargetPathFrame)
        self.SelectTargetDialog = filedialog
        self.ChangeTargetButton: Button = Button(self.TargetPathFrame, text="Browse for target", width=20)

        # init main window
        self.PreviewWindow.title('😈sinner')
        self.PreviewWindow.protocol('WM_DELETE_WINDOW', lambda: self.on_preview_window_close())
        self.PreviewWindow.resizable(width=True, height=True)
        self.PreviewWindow.bind("<KeyRelease>", lambda event: self.on_preview_window_key_release(event))
        self.PreviewWindow.bind("<KeyPress>", lambda event: self.on_preview_window_key_press(event))

        # init preview
        self.PreviewCanvas.bind("<Double-Button-1>", lambda event: self.on_preview_canvas_double_button_1_click())
        self.PreviewCanvas.bind("<Button-2>", lambda event: self.on_preview_canvas_button_2_click())
        self.PreviewCanvas.bind("<Button-3>", lambda event: self.on_preview_canvas_button_3_click())
        self.PreviewCanvas.bind("<Configure>", lambda event: self.on_preview_canvas_resize(event))

        # init generated frames list
        self.PreviewCanvas.pack(fill=BOTH, expand=True)
        self.PreviewFrames.pack(fill=X, expand=False, anchor=NW)

        # init slider
        self.current_position: StringVar = StringVar()
        self.NavigateSlider.configure(command=lambda frame_value: self.on_navigate_slider_change(frame_value))
        self.NavigatePositionLabel.configure(textvariable=self.current_position)
        self.NavigatePositionLabel.pack(anchor=NE, side=LEFT)
        self.RunButton.configure(command=lambda: self.on_self_run_button_press())
        self.RunButton.pack(anchor=NE, side=LEFT)
        self.PreviewButton.configure(command=lambda: self.on_preview_button_press())
        self.PreviewButton.pack(anchor=NE, side=LEFT)
        self.SaveButton.configure(command=lambda: self.on_save_button_press())
        self.SaveButton.pack(anchor=NE, side=LEFT)
        self.NavigateSliderFrame.pack(fill=X)

        # init source selection control set
        self.SourcePathEntry.insert(END, self.GUIModel.source_path)
        self.SourcePathEntry.configure(state="readonly")
        self.SourcePathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeSourceButton.configure(command=lambda: self.on_change_source_button_press())
        self.ChangeSourceButton.pack(side=RIGHT)
        self.SourcePathFrame.pack(fill=X)

        # init target selection control set
        self.TargetPathEntry.insert(END, self.GUIModel.target_path)
        self.TargetPathEntry.configure(state="readonly")
        self.TargetPathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeTargetButton.configure(command=lambda: self.on_change_target_button_press())
        self.ChangeTargetButton.pack(side=LEFT)
        self.TargetPathFrame.pack(fill=X)

    def show(self) -> CTk:
        self.update_preview(self.NavigateSlider.position)
        self.PreviewCanvas.adjust_size()
        return self.PreviewWindow

    # Control events handlers

    @staticmethod
    def on_preview_window_close() -> None:
        quit()

    def on_preview_window_key_release(self, event: Event) -> None:  # type: ignore[type-arg]
        if event.keycode == 37 or event.keycode == 39:
            self.update_preview(self.NavigateSlider.position)

    def on_preview_window_key_press(self, event: Event) -> None:  # type: ignore[type-arg]
        if event.keycode == 37:
            self.NavigateSlider.set(max(1, self.NavigateSlider.position - 1))
        if event.keycode == 39:
            self.NavigateSlider.set(min(self.NavigateSlider.to, self.NavigateSlider.position + 1))
        self.current_position.set(f'{self.NavigateSlider.position}/{self.NavigateSlider.to}')

    def on_preview_canvas_double_button_1_click(self):
        self.update_preview(int(self.NavigateSlider.get()), True)

    def on_preview_canvas_button_2_click(self):
        self.change_source()
        self.update_preview(self.NavigateSlider.position, True)

    def on_preview_canvas_button_3_click(self):
        self.change_target()

    def on_preview_canvas_resize(self, event):
        self.PreviewCanvas.show_frame(resize=(event.width, event.height))

    def on_navigate_slider_change(self, frame_value):
        self.update_preview(int(frame_value))

    def on_self_run_button_press(self):
        self.GUIModel.play(self.NavigateSlider.position)

    def on_preview_button_press(self):
        self.update_preview(self.NavigateSlider.position, True)

    def on_save_button_press(self):
        save_file = filedialog.asksaveasfilename(title='Save frame', defaultextension='png')
        if save_file != ' ':
            self.PreviewCanvas.save_to_file(save_file)

    def on_change_source_button_press(self):
        self.change_source()
        self.update_preview(self.NavigateSlider.position, True)

    def on_change_target_button_press(self):
        self.change_target()

    def on_preview_frames_thumbnail_click(self, frame_number: int, thumbnail_index: int):
        frames = self.GUIModel.get_previews(frame_number)
        if frames:
            self.PreviewCanvas.show_frame(frames[thumbnail_index][0])

    # controls manipulation methods
    def update_preview(self, frame_number: int = 0, processed: bool = False) -> None:
        frames = self.GUIModel.get_frames(frame_number, processed)
        if frames:
            if processed:
                if self.show_frames_widget is True:
                    self.PreviewFrames.show([FrameThumbnail(
                        frame=frame[0],
                        caption=frame[1],
                        position=frame_number,
                        onclick=self.on_preview_frames_thumbnail_click
                    ) for frame in frames])
                self.PreviewCanvas.show_frame(frames[-1][0])
            else:
                self.PreviewCanvas.show_frame(frames[-1][0])
        else:
            self.PreviewCanvas.photo_image = None
        self.current_position.set(f'{frame_number}/{self.NavigateSlider.to}')

    def change_source(self) -> None:
        selected_file = self.SelectSourceDialog.askopenfilename(title='Select a source', initialdir=self.GUIModel.source_dir)
        if selected_file != '':
            self.GUIModel.source_path = selected_file
            self.GUIModel.clear_previews()

            self.SourcePathEntry.configure(state=NORMAL)
            self.SourcePathEntry.delete(0, END)
            self.SourcePathEntry.insert(END, selected_file)
            self.SourcePathEntry.configure(state="readonly")

    def change_target(self) -> None:
        selected_file = self.SelectTargetDialog.askopenfilename(title='Select a target', initialdir=self.GUIModel.target_dir)
        if selected_file != '':
            self.GUIModel.target_path = selected_file
            # self._extractor_handler = None
            self.update_slider_bounds()
            self.update_preview(self.NavigateSlider.position, True)
            self.TargetPathEntry.configure(state=NORMAL)
            self.TargetPathEntry.delete(0, END)
            self.TargetPathEntry.insert(END, selected_file)
            self.TargetPathEntry.configure(state="readonly")
            self.GUIModel.clear_previews()

    def update_slider_bounds(self) -> None:
        if is_image(self.GUIModel.target_path):
            self.NavigateSlider.configure(to=1)
            self.NavigateSlider.set(1)
            self.NavigateSlider.pack_forget()
        if is_video(self.GUIModel.target_path):
            self.NavigateSlider.configure(to=self.GUIModel.frame_handler.fc)
            self.NavigateSlider.pack(anchor=NW, side=LEFT, expand=True, fill=BOTH)
            self.NavigateSlider.set(self.GUIModel.frame_handler.fc / 2)
        self.current_position.set(f'{self.NavigateSlider.position}/{self.NavigateSlider.to}')
