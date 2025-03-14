import tempfile
from argparse import Namespace
from tkinter import filedialog, LEFT, Button, Frame, BOTH, StringVar, NW, X, Event, TOP, CENTER, Menu, CASCADE, COMMAND, RADIOBUTTON, CHECKBUTTON, SEPARATOR, BooleanVar, RIDGE, BOTTOM, NE
from tkinter.ttk import Spinbox, Label, Notebook
from typing import List

from customtkinter import CTk
from psutil import WINDOWS

from sinner.gui.controls.FramePlayer.BaseFramePlayer import ROTATE_90_CLOCKWISE, ROTATE_180, ROTATE_90_COUNTERCLOCKWISE
from sinner.gui.controls.FramePosition.FrameSlider import FrameSlider
from sinner.gui.controls.ThumbnailWidget.SourcesThumbnailWidget import SourcesThumbnailWidget
from sinner.gui.controls.ThumbnailWidget.TargetsThumbnailWidget import TargetsThumbnailWidget
from sinner.models.Event import Event as SinnerEvent
from sinner.gui.GUIModel import GUIModel
from sinner.gui.controls.FramePosition.BaseFramePosition import BaseFramePosition
from sinner.gui.controls.FramePosition.SliderFramePosition import SliderFramePosition
from sinner.gui.controls.StatusBar import StatusBar
from sinner.gui.controls.TextBox import TextBox
from sinner.models.Config import Config
from sinner.models.audio.BaseAudioBackend import BaseAudioBackend
from sinner.utilities import is_int, get_app_dir, get_type_extensions, is_image, is_dir, get_directory_file_list, halt, is_video
from sinner.validators.AttributeLoader import Rules, AttributeLoader


# GUI View

class GUIForm(AttributeLoader):
    # class attributes
    parameters: Namespace
    GUIModel: GUIModel
    StatusBar: StatusBar
    # SourcesLibraryWnd: SourcesLibraryForm
    SourcesLibrary: SourcesThumbnailWidget
    TargetsLibrary: TargetsThumbnailWidget

    topmost: bool
    show_frames_widget: bool
    show_sources_library: bool
    fw_height: int
    fw_width: int
    geometry: str
    state: str  # currently ignored, see issue #100
    sources_library: List[str]
    targets_library: List[str]
    show_progress: bool = False

    _event_player_window_closed: SinnerEvent  # the event when the player window is closed (forwarded via GUIModel)

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
                'parameter': {'controls-state'},
                'attribute': 'state',
            },
            {
                'parameter': {'show-frames-widget', 'frames-widget'},
                'attribute': 'show_frames_widget',
                'default': True,
                'help': 'Show processed frames widget'
            },
            {
                'parameter': {'show-sources-widget', 'show-sources-library', 'sources-widget'},
                'attribute': 'show_sources_library',
                'default': False,
                'help': 'Show the sources library widget'
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
                'parameter': {'sources-library'},
                'attribute': 'sources_library',
                'help': 'The paths to the source files/folders to use in the sources library'
            },
            {
                'parameter': {'targets-library'},
                'attribute': 'targets_library',
                'help': 'The paths to the target files/folders to use in the targets library'
            },
            {
                'parameter': {'progress', 'show-progress'},
                'default': False,
                'attribute': 'show_progress',
                'help': 'Show processing progress indicator (experimental)'
            },
            {
                'module_help': 'GUI Form'
            }
        ]

    def __init__(self, parameters: Namespace):
        if WINDOWS:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]  # it is a library method fixes the issue with different DPIs. Check ignored for non-windows PC like GitHub CI
        self.parameters = parameters
        super().__init__(parameters)
        #  Main window
        self.GUIWindow: CTk = CTk()  # the main window
        if self.geometry:
            self.GUIWindow.geometry(self.geometry)
        # if self.state:
        #     self.GUIWindow.wm_state(self.state)
        self.GUIWindow.iconbitmap(default=get_app_dir("sinner/gui/icons/sinner.ico"))  # the taskbar icon may not be changed due tkinter limitations
        # self.GUIWindow.iconphoto(True, PhotoImage(file=get_app_dir("sinner/gui/icons/sinner_64.png")))  # the taskbar icon may not be changed due tkinter limitations
        self.GUIWindow.title('sinner controls')
        self.GUIWindow.minsize(500, 130)
        self.GUIWindow.protocol('WM_DELETE_WINDOW', lambda: on_player_window_close())
        self._event_player_window_closed = SinnerEvent(on_set_callback=lambda: on_player_window_close())

        self.NavigationFrame: Frame = Frame(self.GUIWindow)  # it is a frame for navigation control and progressbar

        self.StatusBar = StatusBar(self.GUIWindow, borderwidth=1, relief=RIDGE, items={"Target resolution": "", "Render size": ""})
        self.GUIModel = GUIModel(parameters, status_callback=lambda name, value: self.StatusBar.item(name, value), on_close_event=self._event_player_window_closed)

        def on_player_window_close() -> None:
            self.GUIModel.player_stop(wait=True)
            halt()

        self.GUIWindow.bind("<Configure>", lambda event: on_player_window_configure(event))
        self.GUIWindow.bind("<FocusIn>", lambda event: on_player_window_focus_in(event))

        # noinspection PyUnusedLocal
        def on_player_window_configure(event: Event) -> None:  # type: ignore[type-arg]
            if self.GUIWindow.wm_state() != 'zoomed':
                Config(self.parameters).set_key(self.__class__.__name__, 'controls-geometry', self.GUIWindow.geometry())
            Config(self.parameters).set_key(self.__class__.__name__, 'controls-state', self.GUIWindow.wm_state())

        # noinspection PyUnusedLocal
        def on_player_window_focus_in(event: Event) -> None:  # type: ignore[type-arg]
            if self.GUIModel:
                self.GUIModel.Player.bring_to_front()

        self.GUIWindow.resizable(width=True, height=True)
        self.GUIWindow.bind("<KeyRelease>", lambda event: on_player_window_key_release(event))

        def on_player_window_key_release(event: Event) -> None:  # type: ignore[type-arg]
            if event.keycode == 37:  # left arrow
                self.NavigateSlider.position = max(1, self.NavigateSlider.position - self.NavigateSlider.to // 100)
                self.GUIModel.rewind(self.NavigateSlider.position)
            if event.keycode == 39:  # right arrow
                self.GUIModel.rewind(self.NavigateSlider.position)
                self.NavigateSlider.position = min(self.NavigateSlider.to, self.NavigateSlider.position + self.NavigateSlider.to // 100)
            if event.keycode == 32:  # space bar
                on_self_run_button_press()

        # Navigation slider
        self.NavigateSlider: BaseFramePosition = FrameSlider(self.NavigationFrame, from_=1, variable=self.GUIModel.position, command=lambda position: self.GUIModel.rewind(int(position)), progress=self.show_progress)

        # Controls frame and contents
        self.BaseFrame: Frame = Frame(self.GUIWindow)  # it is a frame that holds all static controls with fixed size, such as main buttons and selectors
        self.WidgetsFrame: Frame = Frame(self.GUIWindow)  # it is a frame for dynamic controls which can be hidden, like library widget

        self.ButtonsFrame = Frame(self.BaseFrame)
        self.RunButton: Button = Button(self.ButtonsFrame, text="PLAY", width=10, command=lambda: on_self_run_button_press())

        def on_self_run_button_press() -> None:
            if self.GUIModel.player_is_started:
                self.GUIModel.player_stop()
                self.RunButton.configure(text="PLAY")
            else:
                self.GUIModel.player_start(start_frame=self.NavigateSlider.position)
                self.RunButton.configure(text="STOP")

        self.ControlsFrame = Frame(self.BaseFrame)

        self.SubControlsFrame = Frame(self.ControlsFrame)

        self.QualityScaleLabel: Label = Label(self.SubControlsFrame, text="Quality scale:")

        self.QualityScaleSpinbox: Spinbox = Spinbox(self.SubControlsFrame, from_=1, to=100, increment=1, command=lambda: self.on_quality_scale_change(int(self.QualityScaleSpinbox.get())))
        self.QualityScaleSpinbox.bind('<KeyRelease>', lambda event: self.on_quality_scale_change(int(self.QualityScaleSpinbox.get())))
        self.QualityScaleSpinbox.set(self.GUIModel.quality)

        # empty space to divide controls

        self.EmptyDivisor: Label = Label(self.SubControlsFrame)

        # Volume slider
        self.VolumeLabel: Label = Label(self.SubControlsFrame, text="Vol:")
        self.VolumeSlider: BaseFramePosition = SliderFramePosition(self.SubControlsFrame, from_=0, to=100, variable=self.GUIModel.volume, command=lambda position: self.GUIModel.set_volume(int(position)))

        # source/target selection controls
        self.SourcePathFrame: Frame = Frame(self.ControlsFrame, borderwidth=2)
        self.SourcePathEntry: TextBox = TextBox(self.SourcePathFrame, state='readonly')
        self.SelectSourceDialog = filedialog
        self.ChangeSourceButton: Button = Button(self.SourcePathFrame, text="Browse for source", width=20, command=lambda: self.change_source())

        self.TargetPathFrame: Frame = Frame(self.ControlsFrame, borderwidth=2)
        self.TargetPathEntry: TextBox = TextBox(self.TargetPathFrame, state='readonly')
        self.SelectTargetDialog = filedialog
        self.ChangeTargetButton: Button = Button(self.TargetPathFrame, text="Browse for target", width=20, command=lambda: self.change_target())

        # Library widgets

        self.LibraryNotebook: Notebook = Notebook(self.WidgetsFrame)
        self.SourcesLibraryFrame = Frame(self.LibraryNotebook, borderwidth=2)
        self.LibraryNotebook.add(self.SourcesLibraryFrame, text='Sources')

        self.TargetsLibraryFrame = Frame(self.LibraryNotebook, borderwidth=2)
        self.LibraryNotebook.add(self.TargetsLibraryFrame, text='Targets')
        self.SourcesLibrary = SourcesThumbnailWidget(self.SourcesLibraryFrame, temp_dir=vars(self.parameters).get('temp_dir', tempfile.gettempdir()), click_callback=self._set_source)
        self.TargetsLibrary = TargetsThumbnailWidget(self.TargetsLibraryFrame, temp_dir=vars(self.parameters).get('temp_dir', tempfile.gettempdir()), click_callback=self._set_target)

        # self.GUIModel.status_bar = self.StatusBar

        # Menus
        self.MainMenu: Menu = Menu(self.GUIWindow)
        self.OperationsSubMenu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.OperationsSubMenu, label='Frame')  # type: ignore[no-untyped-call]  # it is a library method
        self.OperationsSubMenu.add(COMMAND, label='Save as png', command=lambda: save_current_frame())  # type: ignore[no-untyped-call]  # it is a library method
        self.OperationsSubMenu.add(COMMAND, label='Reprocess', command=lambda: self.GUIModel.update_preview(True))  # type: ignore[no-untyped-call]  # it is a library method

        def save_current_frame() -> None:
            save_file = filedialog.asksaveasfilename(title='Save frame', defaultextension='png')
            if save_file != '':
                self.GUIModel.Player.save_to_file(save_file)

        self.RotateModeVar: StringVar = StringVar(value="0°")

        self.RotateSubMenu: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.RotateSubMenu, label='Rotation')  # type: ignore[no-untyped-call]  # it is a library method
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label="0°", command=lambda: set_rotate_mode(None))  # type: ignore[no-untyped-call]  # it is a library method
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label="90°", command=lambda: set_rotate_mode(ROTATE_90_CLOCKWISE))  # type: ignore[no-untyped-call]  # it is a library method
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label="180°", command=lambda: set_rotate_mode(ROTATE_180))  # type: ignore[no-untyped-call]  # it is a library method
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label="270°", command=lambda: set_rotate_mode(ROTATE_90_COUNTERCLOCKWISE))  # type: ignore[no-untyped-call]  # it is a library method

        def set_rotate_mode(mode: int | None) -> None:
            self.GUIModel.Player.rotate = mode

        self.SoundEnabledVar: BooleanVar = BooleanVar(value=self.GUIModel.enable_sound())

        self.SoundSubMenu: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.SoundSubMenu, label='Sound')  # type: ignore[no-untyped-call]  # it is a library method
        self.SoundSubMenu.add(CHECKBUTTON, variable=self.SoundEnabledVar, label='Enable sound', command=lambda: self.GUIModel.enable_sound(self.SoundEnabledVar.get()))  # type: ignore[no-untyped-call]  # it is a library method
        self.SoundSubMenu.add(SEPARATOR)  # type: ignore[no-untyped-call]  # it is a library method
        self.SoundSubMenu.add(COMMAND, label='Volume up', command=lambda: increase_volume())  # type: ignore[no-untyped-call]  # it is a library method
        self.SoundSubMenu.add(COMMAND, label='Volume down', command=lambda: decrease_volume())  # type: ignore[no-untyped-call]  # it is a library method

        def increase_volume() -> None:
            if self.GUIModel.volume.get() < 100:
                self.GUIModel.volume.set(self.GUIModel.volume.get() + 1)

        def decrease_volume() -> None:
            if self.GUIModel.volume.get() > 0:
                self.GUIModel.volume.set(self.GUIModel.volume.get() - 1)

        self.SoundSubMenu.add(SEPARATOR)  # type: ignore[no-untyped-call]  # it is a library method
        self.AudioBackendVar: StringVar = StringVar(value=self.GUIModel.audio_backend)

        self.AudioBackendSelectionMenu: Menu = Menu(self.SoundSubMenu, tearoff=False)
        for available_backend in BaseAudioBackend.list():
            self.AudioBackendSelectionMenu.add(RADIOBUTTON, variable=self.AudioBackendVar, label=available_backend, command=lambda: switch_audio_backend(available_backend))  # type: ignore[no-untyped-call]  # it is a library method

        def switch_audio_backend(backend: str) -> None:
            self.GUIModel.audio_backend = backend

        self.SoundSubMenu.add(CASCADE, menu=self.AudioBackendSelectionMenu, label='Audio backend')  # type: ignore[no-untyped-call]  # it is a library method

        self.StayOnTopVar: BooleanVar = BooleanVar(value=self.topmost)
        self.SourceLibraryVar: BooleanVar = BooleanVar(value=self.show_sources_library)

        self.ToolsSubMenu: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.ToolsSubMenu, label='Tools')  # type: ignore[no-untyped-call]  # it is a library method
        self.ToolsSubMenu.add(CHECKBUTTON, label='Stay on top', variable=self.StayOnTopVar, command=lambda: self.set_topmost(self.StayOnTopVar.get()))  # type: ignore[no-untyped-call]  # it is a library method
        # self.ToolsSubMenu.add(CHECKBUTTON, label='Sources library', variable=self.SourceLibraryVar, command=lambda: self.SourcesLibraryWnd.show(show=self.SourceLibraryVar.get()))  # type: ignore[no-untyped-call]  # it is a library method

        # self.ToolsSubMenu.add(CHECKBUTTON, label='go fullscreen', command=lambda: self.player.set_fullscreen())
        #
        self.LibraryMenu: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.LibraryMenu, label='Library')  # type: ignore[no-untyped-call]  # it is a library method
        self.SourcesLibraryMenu: Menu = Menu(self.LibraryMenu, tearoff=False)
        self.TargetsLibraryMenu: Menu = Menu(self.LibraryMenu, tearoff=False)
        self.LibraryMenu.add(CASCADE, menu=self.SourcesLibraryMenu, label='Sources library')  # type: ignore[no-untyped-call]  # it is a library method
        self.LibraryMenu.add(CASCADE, menu=self.TargetsLibraryMenu, label='Targets library')  # type: ignore[no-untyped-call]  # it is a library method
        self.SourcesLibraryMenu.add(COMMAND, label='Add files', command=lambda: self.add_source_files())  # type: ignore[no-untyped-call]  # it is a library method
        self.SourcesLibraryMenu.add(COMMAND, label='Add a folder', command=lambda: self.add_source_folder())  # type: ignore[no-untyped-call]  # it is a library method
        self.SourcesLibraryMenu.add(SEPARATOR)  # type: ignore[no-untyped-call]  # it is a library method
        self.SourcesLibraryMenu.add(COMMAND, label='Clear', command=lambda: self.source_clear())  # type: ignore[no-untyped-call]  # it is a library method
        self.TargetsLibraryMenu.add(COMMAND, label='Add files', command=lambda: self.add_target_files())  # type: ignore[no-untyped-call]  # it is a library method
        self.TargetsLibraryMenu.add(COMMAND, label='Add a folder', command=lambda: self.add_target_folder())  # type: ignore[no-untyped-call]  # it is a library method
        self.TargetsLibraryMenu.add(SEPARATOR)  # type: ignore[no-untyped-call]  # it is a library method
        self.TargetsLibraryMenu.add(COMMAND, label='Clear', command=lambda: self.target_clear())  # type: ignore[no-untyped-call]  # it is a library method

        self.GUIWindow.configure(menu=self.MainMenu, tearoff=False)

    # maintain the order of window controls
    def draw_controls(self) -> None:
        self.NavigationFrame.pack(fill=X, expand=False, anchor=NW)
        self.NavigateSlider.pack(anchor=NW, side=LEFT, expand=True, fill=BOTH)
        self.update_slider_bounds()

        self.GUIModel.progress_control = self.NavigateSlider.progress

        self.RunButton.pack(side=TOP, fill=BOTH, expand=True)
        self.ButtonsFrame.pack(anchor=CENTER, expand=False, side=LEFT, fill=BOTH)
        self.BaseFrame.pack(anchor=NW, expand=False, side=TOP, fill=X)

        self.QualityScaleLabel.pack(anchor=NW, side=LEFT)
        self.QualityScaleSpinbox.pack(anchor=NW, expand=False, fill=BOTH, side=LEFT)

        self.EmptyDivisor.pack(anchor=CENTER, expand=True, fill=BOTH, side=LEFT)

        self.VolumeLabel.pack(anchor=NE, side=LEFT)
        self.VolumeSlider.pack(anchor=NE, side=LEFT, expand=False, fill=X)
        self.SubControlsFrame.pack(anchor=CENTER, expand=True, fill=BOTH)

        self.SourcePathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeSourceButton.pack(side=LEFT)
        self.SourcePathFrame.pack(fill=X, side=TOP, expand=True)

        self.TargetPathEntry.pack(side=LEFT, expand=True, fill=BOTH)
        self.ChangeTargetButton.pack(side=LEFT)
        self.TargetPathFrame.pack(fill=X, side=TOP, expand=True)

        self.ControlsFrame.pack(side=TOP, fill=BOTH, expand=True)

        self.SourcesLibrary.pack(side=TOP, expand=True, fill=BOTH)
        self.SourcesLibraryFrame.rowconfigure(0, weight=1)
        self.SourcesLibraryFrame.columnconfigure(0, weight=1)
        self.LibraryNotebook.pack(expand=True, fill='both')

        self.TargetsLibrary.pack(side=BOTTOM, expand=True, fill=BOTH)
        self.TargetsLibraryFrame.rowconfigure(0, weight=1)
        self.TargetsLibraryFrame.columnconfigure(0, weight=1)

        self.WidgetsFrame.pack(side=TOP, expand=True, fill=BOTH)

        self.StatusBar.pack(fill=X, side=BOTTOM, expand=False)

    # initialize all secondary windows
    def create_windows(self) -> None:
        pass

    def format_target_info(self) -> str:
        return f"{self.GUIModel.frame_handler.resolution[0]}x{self.GUIModel.frame_handler.resolution[1]}@{round(self.GUIModel.frame_handler.fps, ndigits=3)}"

    def set_topmost(self, on_top: bool = True) -> None:
        self.GUIWindow.wm_attributes("-topmost", on_top)
        self.GUIModel.Player.set_topmost(on_top)

    def show(self) -> CTk:
        self.draw_controls()
        self.SourcePathEntry.set_text(self.GUIModel.source_path)
        self.TargetPathEntry.set_text(self.GUIModel.target_path)
        self.StatusBar.item('Target resolution', self.format_target_info())
        self.GUIModel.update_preview()
        self.create_windows()
        self.GUIWindow.wm_attributes("-topmost", self.topmost)
        self.GUIModel.Player.bring_to_front()
        self.GUIModel.Player.set_topmost(self.topmost)
        if self.geometry:
            self.load_geometry()
        if self.state:
            self.GUIWindow.wm_state(self.state)
        if self.sources_library:
            self.source_library_add(paths=self.sources_library)

        if self.targets_library:
            self.target_library_add(paths=self.targets_library)
        return self.GUIWindow

    def load_geometry(self) -> None:
        self.GUIWindow.update()
        self.GUIWindow.update_idletasks()
        current_size_part, _ = self.GUIWindow.geometry().split('+', 1)
        current_height = int(current_size_part.split('x')[1])
        size_part, position_part = self.geometry.split('+', 1)
        requested_width = int(size_part.split('x')[0])
        self.GUIWindow.geometry(f"{requested_width}x{current_height}+{position_part}")

    def change_source(self) -> bool:
        selected_file = self.SelectSourceDialog.askopenfilename(title='Select a source', initialdir=self.GUIModel.source_dir)
        if selected_file != '':
            self._set_source(selected_file)
            return True
        return False

    def _set_source(self, filename: str) -> None:
        self.GUIModel.source_path = filename
        self.SourcePathEntry.set_text(filename)

    def change_target(self) -> bool:
        selected_file = self.SelectTargetDialog.askopenfilename(title='Select a target', initialdir=self.GUIModel.target_dir)
        if selected_file != '':
            self._set_target(selected_file)
            return True
        return False

    def _set_target(self, filename: str) -> None:
        self.NavigateSlider.position = 1
        self.GUIModel.target_path = filename
        self.update_slider_bounds()
        self.TargetPathEntry.set_text(filename)
        self.on_quality_scale_change(self.GUIModel.quality)
        self.StatusBar.item('Target resolution', self.format_target_info())

    def update_slider_bounds(self) -> None:
        self.NavigateSlider.to = self.GUIModel.frame_handler.fc
        self.NavigateSlider.position = 1
        if self.NavigateSlider.to > 1:
            self.NavigateSlider.enable()
        else:
            self.NavigateSlider.disable()

    def on_quality_scale_change(self, frame_value: int) -> None:
        if frame_value > self.QualityScaleSpinbox.cget('to'):
            frame_value = self.QualityScaleSpinbox.cget('to')
        if frame_value < self.QualityScaleSpinbox.cget('from'):
            frame_value = self.QualityScaleSpinbox.cget('from')
        self.GUIModel.quality = frame_value
        if self.GUIModel.frame_handler.resolution:
            #  the quality applies only when playing, the preview always renders with 100% resolution
            self.StatusBar.item('Render size', f"{self.GUIModel.quality}% ({int(self.GUIModel.frame_handler.resolution[0] * self.GUIModel.quality / 100)}x{int(self.GUIModel.frame_handler.resolution[1] * self.GUIModel.quality / 100)})")

    def source_library_add(self, paths: List[str], reload: bool = False) -> None:
        """
        Add something to the sources library
        :param paths: each path can point to an image or a folder with images
        :param reload: True for reloading library from given paths
        """
        if reload:
            self.SourcesLibrary.clear_thumbnails()

        for path in paths:
            if is_dir(path):
                for dir_file in get_directory_file_list(path, is_image):
                    self.SourcesLibrary.add_thumbnail(source_path=dir_file)
            else:
                self.SourcesLibrary.add_thumbnail(source_path=path)

    def add_source_files(self) -> None:
        image_extensions = get_type_extensions('image/')
        file_paths = filedialog.askopenfilenames(
            title="Select files to add to sources",
            filetypes=[('Image files', image_extensions), ('All files', '*.*')],
            initialdir=self.GUIModel.source_dir
        )
        if file_paths:
            self.source_library_add(paths=list(file_paths))

    def add_source_folder(self) -> None:
        directory = filedialog.askdirectory(
            title="Select a directory to add sources",
            initialdir=self.GUIModel.source_dir
        )
        if directory:
            self.source_library_add(paths=[directory])

    def source_clear(self) -> None:
        self.SourcesLibrary.clear_thumbnails()

    def target_library_add(self, paths: List[str], reload: bool = False) -> None:
        """
        Add something to the sources library
        :param paths: each path can point to an image or a folder with images
        :param reload: True for reloading library from given paths
        """
        if reload:
            self.TargetsLibrary.clear_thumbnails()

        for path in paths:
            if is_dir(path):
                for dir_file in get_directory_file_list(path, is_video):
                    self.TargetsLibrary.add_thumbnail(source_path=dir_file)
            else:
                self.TargetsLibrary.add_thumbnail(source_path=path)

    def add_target_files(self) -> None:
        file_paths = filedialog.askopenfilenames(
            title="Select files to add to targets",
            filetypes=[('All files', '*.*')],
            initialdir=self.GUIModel.target_dir
        )
        if file_paths:
            self.target_library_add(paths=list(file_paths))

    def add_target_folder(self) -> None:
        directory = filedialog.askdirectory(
            title="Select a directory to add targets",
            initialdir=self.GUIModel.target_dir
        )
        if directory:
            self.target_library_add(paths=[directory])

    def target_clear(self) -> None:
        self.TargetsLibrary.clear_thumbnails()
