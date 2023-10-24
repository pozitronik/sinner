from argparse import Namespace
from tkinter import filedialog, LEFT, Button, Frame, BOTH, RIGHT, StringVar, NE, NW, X, Event

from customtkinter import CTk

from sinner.Status import Status
from sinner.gui.GUIModel import GUIModel
from sinner.gui.controls.FrameThumbnail import FrameThumbnail
from sinner.gui.controls.ImageList import ImageList
from sinner.gui.controls.NavigateSlider import NavigateSlider
from sinner.gui.controls.PreviewCanvas import PreviewCanvas
from sinner.gui.controls.SimpleStatusBar import SimpleStatusBar
from sinner.gui.controls.TextBox import TextBox, READONLY
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
        self.GUIWindow: CTk = CTk()  # the main window
        self.PreviewCanvas: PreviewCanvas = PreviewCanvas(self.GUIWindow)  # the main preview
        self.PreviewFrames: ImageList = ImageList(parent=self.GUIWindow, size=(self.fw_width, self.fw_height))  # the preview of processed frames
        self.NavigateSlider: NavigateSlider = NavigateSlider(self.GUIWindow)
        # button controls
        self.RunButton: Button = Button(self.GUIWindow, text="PLAY", compound=LEFT)
        self.PreviewButton: Button = Button(self.GUIWindow, text="TEST", compound=LEFT)
        self.SaveButton: Button = Button(self.GUIWindow, text="SAVE", compound=LEFT)
        # player controls - will be moved to a separate sub-window
        self.PlayerFrame: Frame = Frame(self.GUIWindow, borderwidth=2)
        self.QualitySlider: NavigateSlider = NavigateSlider(self.PlayerFrame, to=100)
        self.QualitySlider.pack(anchor=NW, side=LEFT, expand=True, fill=BOTH)
        self.QualitySlider.set(self.GUIModel.quality)

        # source/target selection controls
        self.SourcePathFrame: Frame = Frame(self.GUIWindow, borderwidth=2)
        self.SourcePathEntry: TextBox = TextBox(self.SourcePathFrame)
        self.SelectSourceDialog = filedialog
        self.ChangeSourceButton: Button = Button(self.SourcePathFrame, text="Browse for source", width=20)
        self.TargetPathFrame: Frame = Frame(self.GUIWindow, borderwidth=2)
        self.TargetPathEntry: TextBox = TextBox(self.TargetPathFrame)
        self.SelectTargetDialog = filedialog
        self.ChangeTargetButton: Button = Button(self.TargetPathFrame, text="Browse for target", width=20)
        self.StatusBar: SimpleStatusBar = SimpleStatusBar(self.GUIWindow)
        self.GUIModel.status_bar = self.StatusBar

        # init main window
        self.GUIWindow.title('😈sinner')
        self.GUIWindow.protocol('WM_DELETE_WINDOW', lambda: self.on_preview_window_close())
        self.GUIWindow.resizable(width=True, height=True)
        self.GUIWindow.bind("<KeyRelease>", lambda event: self.on_preview_window_key_release(event))
        self.GUIWindow.bind("<KeyPress>", lambda event: self.on_preview_window_key_press(event))

        # init preview
        self.PreviewCanvas.configure(width=100, height=100)  # set the default canvas size
        self.PreviewCanvas.bind("<Double-Button-1>", lambda event: self.on_preview_canvas_double_button_1_click())
        self.PreviewCanvas.bind("<Button-2>", lambda event: self.on_preview_canvas_button_2_click())
        self.PreviewCanvas.bind("<Button-3>", lambda event: self.on_preview_canvas_button_3_click())
        self.PreviewCanvas.bind("<Configure>", lambda event: self.on_preview_canvas_resize(event))

        # init slider
        self.NavigateSlider.configure(command=lambda frame_value: self.on_navigate_slider_change(frame_value))

        # buttons
        self.RunButton.configure(command=lambda: self.on_self_run_button_press())
        self.PreviewButton.configure(command=lambda: self.on_preview_button_press())
        self.SaveButton.configure(command=lambda: self.on_save_button_press())
        self.ChangeSourceButton.configure(command=lambda: self.on_change_source_button_press())
        self.ChangeTargetButton.configure(command=lambda: self.on_change_target_button_press())

        self.SourcePathEntry.configure(state=READONLY)  # type: ignore[call-overload]
        self.TargetPathEntry.configure(state=READONLY)  # type: ignore[call-overload]

        # player controls
        self.QualitySlider.configure(command=lambda frame_value: self.on_quality_slider_change(frame_value))

    # maintain the order of window controls
    def draw_controls(self) -> None:
        self.PreviewCanvas.pack(fill=BOTH, expand=True)
        self.PreviewFrames.pack(fill=X, expand=False, anchor=NW)
        self.update_slider_bounds()  # also draws slider, if necessary
        self.SaveButton.pack(anchor=NE, side=RIGHT)
        self.PreviewButton.pack(anchor=NE, side=RIGHT)
        self.RunButton.pack(anchor=NE, side=RIGHT)
        self.PlayerFrame.pack(fill=X)
        self.SourcePathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeSourceButton.pack(side=RIGHT)
        self.SourcePathFrame.pack(fill=X)
        self.TargetPathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeTargetButton.pack(side=LEFT)
        self.TargetPathFrame.pack(fill=X)
        self.StatusBar.pack()

    def show(self) -> CTk:
        self.draw_controls()
        self.SourcePathEntry.set_text(self.GUIModel.source_path)
        self.TargetPathEntry.set_text(self.GUIModel.target_path)
        self.StatusBar.set_item('target_res', f"{self.GUIModel.frame_handler.resolution}")
        self.update_preview(self.NavigateSlider.position)
        self.PreviewCanvas.adjust_size()
        return self.GUIWindow

    # Control events handlers

    def on_preview_window_close(self) -> None:
        self.GUIModel.player_stop(True)
        quit()

    def on_preview_window_key_release(self, event: Event) -> None:  # type: ignore[type-arg]
        if event.keycode == 37 or event.keycode == 39:
            self.update_preview(self.NavigateSlider.position)

    def on_preview_window_key_press(self, event: Event) -> None:  # type: ignore[type-arg]
        if event.keycode == 37:
            self.NavigateSlider.position = max(1, self.NavigateSlider.position - 1)
        if event.keycode == 39:
            self.NavigateSlider.position = min(self.NavigateSlider.to, self.NavigateSlider.position + 1)

    def on_preview_canvas_double_button_1_click(self) -> None:
        self.update_preview(self.NavigateSlider.position)

    def on_preview_canvas_button_2_click(self) -> None:
        self.change_source()
        self.update_preview(self.NavigateSlider.position)

    def on_preview_canvas_button_3_click(self) -> None:
        self.change_target()

    def on_preview_canvas_resize(self, event: Event) -> None:  # type: ignore[type-arg]
        self.StatusBar.set_item('view_res', f"{(event.width, event.height)}")
        self.PreviewCanvas.show_frame(resize=(event.width, event.height))

    def on_navigate_slider_change(self, frame_value: float) -> None:
        if self.GUIModel.player_is_playing:
            self.GUIModel.player_stop()
            self.GUIModel.player_start(start_frame=self.NavigateSlider.position, canvas=self.PreviewCanvas, progress_callback=self.NavigateSlider.set)
        else:
            self.update_preview(int(frame_value))

    def on_self_run_button_press(self) -> None:
        if self.GUIModel.player_is_playing:
            self.GUIModel.player_stop()
            self.RunButton.configure(text="PLAY")
        else:
            self.GUIModel.player_start(start_frame=self.NavigateSlider.position, canvas=self.PreviewCanvas, progress_callback=self.NavigateSlider.set)
            self.RunButton.configure(text="STOP")

    def on_preview_button_press(self) -> None:
        self.update_preview(self.NavigateSlider.position, True)

    def on_save_button_press(self) -> None:
        save_file = filedialog.asksaveasfilename(title='Save frame', defaultextension='png')
        if save_file != ' ':
            self.PreviewCanvas.save_to_file(save_file)

    def on_change_source_button_press(self) -> None:
        self.change_source()
        if self.GUIModel.player_is_playing:
            self.GUIModel.player_stop()
            self.GUIModel.player_start(start_frame=self.NavigateSlider.position, canvas=self.PreviewCanvas, progress_callback=self.NavigateSlider.set)
        else:
            self.update_preview(self.NavigateSlider.position)

    def on_change_target_button_press(self) -> None:
        self.change_target()
        if self.GUIModel.player_is_playing:
            self.GUIModel.player_stop()
            self.GUIModel.player_start(start_frame=self.NavigateSlider.position, canvas=self.PreviewCanvas, progress_callback=self.NavigateSlider.set)
        else:
            self.update_preview(self.NavigateSlider.position)

    def on_quality_slider_change(self, frame_value: float) -> None:
        self.GUIModel.quality = int(frame_value)
        #  the quality applies only when playing, the preview always renders with 100% resolution

    def on_preview_frames_thumbnail_click(self, frame_number: int, thumbnail_index: int) -> None:
        frames = self.GUIModel.get_previews(frame_number)
        if frames:
            self.PreviewCanvas.show_frame(frames[thumbnail_index][0])

    # controls manipulation methods
    def update_preview(self, frame_number: int = 0, processed: bool | None = None) -> None:
        if processed is None:
            processed = self.GUIModel.is_processors_loaded
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
                self.PreviewCanvas.show_frame(frames[0][0])
        else:
            self.PreviewCanvas.photo_image = None

    def change_source(self) -> None:
        selected_file = self.SelectSourceDialog.askopenfilename(title='Select a source', initialdir=self.GUIModel.source_dir)
        if selected_file != '':
            self.GUIModel.source_path = selected_file
            self.SourcePathEntry.set_text(selected_file)

    def change_target(self) -> None:
        selected_file = self.SelectTargetDialog.askopenfilename(title='Select a target', initialdir=self.GUIModel.target_dir)
        if selected_file != '':
            self.GUIModel.target_path = selected_file
            # self._extractor_handler = None
            self.update_slider_bounds()
            self.TargetPathEntry.set_text(selected_file)
            self.PreviewCanvas.adjust_size()
            self.StatusBar.set_item('target_res', f"{self.GUIModel.frame_handler.resolution}")

    def update_slider_bounds(self) -> None:
        if is_image(self.GUIModel.target_path):
            self.NavigateSlider.configure.to = 1
            self.NavigateSlider.pack_forget()
        if is_video(self.GUIModel.target_path):
            self.NavigateSlider.to = self.GUIModel.frame_handler.fc
            self.NavigateSlider.pack(anchor=NW, side=LEFT, expand=True, fill=BOTH)
            self.NavigateSlider.position = 0
