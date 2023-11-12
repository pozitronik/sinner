from argparse import Namespace
from tkinter import filedialog, LEFT, Button, Frame, BOTH, RIGHT, StringVar, NW, X, Event, Scale, TOP, HORIZONTAL, CENTER, Menu, CASCADE, COMMAND, RADIOBUTTON, CHECKBUTTON, BooleanVar, RIDGE

from customtkinter import CTk

from sinner.Status import Status
from sinner.gui.GUIModel import GUIModel, FrameMode
from sinner.gui.controls.FramePlayer.BaseFramePlayer import RotateMode
from sinner.gui.controls.FramePosition.BaseFramePosition import BaseFramePosition
from sinner.gui.controls.FramePosition.SliderFramePosition import SliderFramePosition
from sinner.gui.controls.ImageList import ImageList
from sinner.gui.controls.ProgressBarManager import ProgressBarManager
from sinner.gui.controls.StatusBar import StatusBar
from sinner.gui.controls.TextBox import TextBox
from sinner.models.Config import Config
from sinner.utilities import is_int, get_app_dir
from sinner.validators.AttributeLoader import Rules


# GUI View
class GUIForm(Status):
    # class attributes
    parameters: Namespace
    GUIModel: GUIModel
    ProgressBars: ProgressBarManager
    StatusBar: StatusBar

    topmost: bool
    show_frames_widget: bool
    fw_height: int
    fw_width: int
    geometry: str

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'topmost', 'on-top'},
                'attribute': 'topmost',
                'default': False,
                'help': 'Set player on top of other windows'
            },
            {
                'parameter': {'controls-geometry'},
                'attribute': 'geometry',
                'help': 'Window size and position'
            },
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
        self.parameters = parameters
        super().__init__(parameters)
        #  Main window
        self.GUIWindow: CTk = CTk()  # the main window
        self.GUIWindow.iconbitmap(get_app_dir("sinner/gui/icons/sinner.ico"))  # the taskbar icon may not be changed due tkinter limitations
        # self.GUIWindow.iconphoto(True, PhotoImage(file=get_app_dir("sinner/gui/icons/sinner_64.png")))  # the taskbar icon may not be changed due tkinter limitations
        self.GUIWindow.title('sinner controls')
        self.GUIWindow.minsize(500, 0)
        if self.geometry:
            self.GUIWindow.geometry(self.geometry)
        self.GUIWindow.protocol('WM_DELETE_WINDOW', lambda: on_player_window_close())

        def on_player_window_close() -> None:
            self.GUIModel.player_stop(wait=True)
            quit()

        self.GUIWindow.bind("<Configure>", lambda event: on_player_window_configure(event))

        def on_player_window_configure(event: Event) -> None:
            Config(self.parameters).set_key(self.__class__.__name__, 'controls-geometry', self.GUIWindow.geometry())

        self.GUIWindow.resizable(width=True, height=False)
        self.GUIWindow.bind("<KeyRelease>", lambda event: on_player_window_key_release(event))

        self.ProgressBars = ProgressBarManager(self.GUIWindow)
        self.StatusBar = StatusBar(self.GUIWindow, borderwidth=1, relief=RIDGE, items={"Target resolution": "", "Render size": ""})
        self.GUIModel = GUIModel(parameters, pb_control=self.ProgressBars, status_callback=lambda name, value: self.StatusBar.item(name, value))

        def on_player_window_key_release(event: Event) -> None:  # type: ignore[type-arg]
            if event.keycode == 37:  # left arrow
                self.NavigateSlider.position = max(1, self.NavigateSlider.position - self.NavigateSlider.to // 100)
                self.GUIModel.rewind(self.NavigateSlider.position)
            if event.keycode == 39:  # right arrow
                self.GUIModel.rewind(self.NavigateSlider.position)
                self.NavigateSlider.position = min(self.NavigateSlider.to, self.NavigateSlider.position + self.NavigateSlider.to // 100)
            if event.keycode == 32:  # space bar
                on_self_run_button_press()

        # todo: move to a separate window
        self.PreviewFrames: ImageList = ImageList(parent=self.GUIWindow, size=(self.fw_width, self.fw_height))  # the preview of processed frames

        # Navigation slider
        self.NavigateSlider: BaseFramePosition = SliderFramePosition(self.GUIWindow, from_=1, variable=self.GUIModel.position, command=lambda position: self.GUIModel.rewind(int(position)))

        # Controls frame and contents
        self.ControlsFrame = Frame(self.GUIWindow)
        self.RunButton: Button = Button(self.ControlsFrame, text="PLAY", compound=LEFT, command=lambda: on_self_run_button_press())

        def on_self_run_button_press() -> None:
            if self.GUIModel.player_is_started:
                self.GUIModel.player_stop()
                self.RunButton.configure(text="PLAY")
            else:
                self.GUIModel.player_start(start_frame=self.NavigateSlider.position)
                self.RunButton.configure(text="STOP")

        self.QualityScale: Scale = Scale(self.ControlsFrame, showvalue=False, from_=1, to=100, length=300, orient=HORIZONTAL, command=lambda frame_value: self.on_quality_scale_change(int(frame_value)))
        self.QualityScale.set(self.GUIModel.quality)

        # source/target selection controls
        self.SourcePathFrame: Frame = Frame(self.GUIWindow, borderwidth=2)
        self.SourcePathEntry: TextBox = TextBox(self.SourcePathFrame, state='readonly')
        self.SelectSourceDialog = filedialog
        self.ChangeSourceButton: Button = Button(self.SourcePathFrame, text="Browse for source", width=20, command=lambda: self.change_source())

        self.TargetPathFrame: Frame = Frame(self.GUIWindow, borderwidth=2)
        self.TargetPathEntry: TextBox = TextBox(self.TargetPathFrame, state='readonly')
        self.SelectTargetDialog = filedialog
        self.ChangeTargetButton: Button = Button(self.TargetPathFrame, text="Browse for target", width=20, command=lambda: self.change_target())

        # self.GUIModel.status_bar = self.StatusBar

        self.MainMenu = Menu(self.GUIWindow)
        self.OperationsSubMenu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.OperationsSubMenu, label='Frame')  # type: ignore[no-untyped-call]  # it is a library method
        self.OperationsSubMenu.add(COMMAND, label='Save as png', command=lambda: save_current_frame())  # type: ignore[no-untyped-call]  # it is a library method
        self.OperationsSubMenu.add(COMMAND, label='Reprocess', command=lambda: self.GUIModel.update_preview(True))  # type: ignore[no-untyped-call]  # it is a library method

        def save_current_frame() -> None:
            save_file = filedialog.asksaveasfilename(title='Save frame', defaultextension='png')
            if save_file != '':
                self.GUIModel.Player.save_to_file(save_file)

        self.FrameModeVar: StringVar = StringVar(value=self.GUIModel.frame_mode.value)

        self.ModeSubMenu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.ModeSubMenu, label='Playback mode')  # type: ignore[no-untyped-call]  # it is a library method
        self.ModeSubMenu.add(RADIOBUTTON, variable=self.FrameModeVar, label=FrameMode.ALL.value, command=lambda: set_framerate_mode(FrameMode.ALL))  # type: ignore[no-untyped-call]  # it is a library method
        self.ModeSubMenu.add(RADIOBUTTON, variable=self.FrameModeVar, label=FrameMode.SKIP.value, command=lambda: set_framerate_mode(FrameMode.SKIP))  # type: ignore[no-untyped-call]  # it is a library method

        def set_framerate_mode(mode: FrameMode) -> None:
            self.GUIModel.frame_mode = mode

        self.RotateModeVar: StringVar = StringVar(value=RotateMode.ROTATE_0.value)

        self.RotateSubMenu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.RotateSubMenu, label='Rotation')  # type: ignore[no-untyped-call]  # it is a library method
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label=RotateMode.ROTATE_0.value, command=lambda: set_rotate_mode(RotateMode.ROTATE_0))  # type: ignore[no-untyped-call]  # it is a library method
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label=RotateMode.ROTATE_90.value, command=lambda: set_rotate_mode(RotateMode.ROTATE_90))  # type: ignore[no-untyped-call]  # it is a library method
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label=RotateMode.ROTATE_180.value, command=lambda: set_rotate_mode(RotateMode.ROTATE_180))  # type: ignore[no-untyped-call]  # it is a library method
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label=RotateMode.ROTATE_270.value, command=lambda: set_rotate_mode(RotateMode.ROTATE_270))  # type: ignore[no-untyped-call]  # it is a library method

        def set_rotate_mode(mode: RotateMode) -> None:
            self.GUIModel.Player.rotate = mode

        self.StayOnTopVar: BooleanVar = BooleanVar(value=self.topmost)

        self.ToolsSubMenu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.ToolsSubMenu, label='Tools')  # type: ignore[no-untyped-call]  # it is a library method
        self.ToolsSubMenu.add(CHECKBUTTON, label='Stay on top', variable=self.StayOnTopVar, command=lambda: set_on_top())  # type: ignore[no-untyped-call]  # it is a library method

        def set_on_top() -> None:
            self.GUIWindow.wm_attributes("-topmost", self.StayOnTopVar.get())
            self.GUIModel.Player.set_topmost(self.StayOnTopVar.get())

        # self.ToolsSubMenu.add(CHECKBUTTON, label='Frames previews')
        #
        # self.ToolsSubMenu.add(CHECKBUTTON, label='go fullscreen', command=lambda: self.player.set_fullscreen())
        #
        # self.ToolsSubMenu.add(CHECKBUTTON, label='Source selection', state=DISABLED)
        # self.ToolsSubMenu.add(CHECKBUTTON, label='Target selection', state=DISABLED)

        self.GUIWindow.configure(menu=self.MainMenu, tearoff=False)

    # maintain the order of window controls
    def draw_controls(self) -> None:
        # self.NavigateSlider.pack(anchor=CENTER, side=TOP, expand=False, fill=X)
        self.NavigateSlider.pack(anchor=NW, side=LEFT, expand=True, fill=BOTH)
        self.PreviewFrames.pack(fill=X, expand=False, anchor=NW)
        self.update_slider_bounds()
        self.ControlsFrame.pack(anchor=CENTER, expand=False, fill=X, side=TOP)
        self.RunButton.pack(anchor=CENTER, side=LEFT)
        self.QualityScale.pack(anchor=CENTER, expand=True, fill=BOTH, side=LEFT)
        self.SourcePathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeSourceButton.pack(side=RIGHT)
        self.SourcePathFrame.pack(fill=X, side=TOP)
        self.TargetPathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeTargetButton.pack(side=LEFT)
        self.TargetPathFrame.pack(fill=X, side=TOP)
        self.StatusBar.pack()

    def format_target_info(self) -> str:
        return f"{self.GUIModel.frame_handler.resolution[0]}x{self.GUIModel.frame_handler.resolution[1]}@{round(self.GUIModel.frame_handler.fps, ndigits=3)}"

    def show(self) -> CTk:
        self.draw_controls()
        self.SourcePathEntry.set_text(self.GUIModel.source_path)
        self.TargetPathEntry.set_text(self.GUIModel.target_path)
        self.StatusBar.item('Target resolution', self.format_target_info())
        self.GUIModel.update_preview()
        self.GUIWindow.wm_attributes("-topmost", self.topmost)
        self.GUIModel.Player.set_topmost()
        return self.GUIWindow

    def change_source(self) -> bool:
        selected_file = self.SelectSourceDialog.askopenfilename(title='Select a source', initialdir=self.GUIModel.source_dir)
        if selected_file != '':
            self.GUIModel.source_path = selected_file
            self.SourcePathEntry.set_text(selected_file)
            return True
        return False

    def change_target(self) -> bool:
        selected_file = self.SelectTargetDialog.askopenfilename(title='Select a target', initialdir=self.GUIModel.target_dir)
        if selected_file != '':
            self.NavigateSlider.position = 1
            self.GUIModel.target_path = selected_file
            self.update_slider_bounds()
            self.TargetPathEntry.set_text(selected_file)
            self.on_quality_scale_change(self.GUIModel.quality)
            self.StatusBar.item('Target resolution', self.format_target_info())
            return True
        return False

    def update_slider_bounds(self) -> None:
        self.NavigateSlider.to = self.GUIModel.frame_handler.fc
        self.NavigateSlider.position = 1
        if self.NavigateSlider.to > 1:
            self.NavigateSlider.enable()
        else:
            self.NavigateSlider.disable()

    def on_quality_scale_change(self, frame_value: int) -> None:
        self.GUIModel.quality = frame_value
        if self.GUIModel.frame_handler.resolution:
            #  the quality applies only when playing, the preview always renders with 100% resolution
            self.StatusBar.item('Render size', f"{self.GUIModel.quality}% ({int(self.GUIModel.frame_handler.resolution[0] * self.GUIModel.quality / 100)}x{int(self.GUIModel.frame_handler.resolution[1] * self.GUIModel.quality / 100)})")
