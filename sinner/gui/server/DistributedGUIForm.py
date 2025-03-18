import tempfile
from argparse import Namespace
from tkinter import filedialog, LEFT, Button, Frame, BOTH, StringVar, NW, X, Event, TOP, CENTER, Menu, CASCADE, COMMAND, RADIOBUTTON, CHECKBUTTON, SEPARATOR, BooleanVar, RIDGE, BOTTOM, NE
from tkinter.ttk import Spinbox, Label, Notebook
from typing import List, Optional

from customtkinter import CTk
from psutil import WINDOWS

from sinner.gui.controls.FramePlayer.BaseFramePlayer import ROTATE_90_CLOCKWISE, ROTATE_180, ROTATE_90_COUNTERCLOCKWISE
from sinner.gui.controls.FramePosition.FrameSlider import FrameSlider
from sinner.gui.controls.ThumbnailWidget.SourcesThumbnailWidget import SourcesThumbnailWidget
from sinner.gui.controls.ThumbnailWidget.TargetsThumbnailWidget import TargetsThumbnailWidget
from sinner.models.Event import Event as SinnerEvent
from sinner.gui.controls.FramePosition.BaseFramePosition import BaseFramePosition
from sinner.gui.controls.FramePosition.SliderFramePosition import SliderFramePosition
from sinner.gui.controls.StatusBar import StatusBar
from sinner.gui.controls.TextBox import TextBox
from sinner.models.Config import Config
from sinner.models.audio.BaseAudioBackend import BaseAudioBackend
from sinner.utilities import is_int, get_app_dir, get_type_extensions, is_image, is_dir, get_directory_file_list, halt, is_video
from sinner.validators.AttributeLoader import Rules, AttributeLoader

from DistributedGUIModel import DistributedGUIModel, create_distributed_gui_model
from DistributedProcessingSystem import DistributedProcessingSystem


class DistributedGUIForm(AttributeLoader):
    """
    Полностью новая реализация GUI для использования распределенной обработки.
    Не использует наследование от стандартного GUIForm.
    """

    # Configuration variables
    parameters: Namespace
    GUIModel: DistributedGUIModel
    StatusBar: StatusBar
    SourcesLibrary: SourcesThumbnailWidget
    TargetsLibrary: TargetsThumbnailWidget

    topmost: bool
    show_frames_widget: bool
    show_sources_library: bool
    fw_height: int
    fw_width: int
    geometry: str
    state: str
    sources_library: List[str]
    targets_library: List[str]
    show_progress: bool = False
    zmq_endpoint: str
    server_mode: str

    _event_player_window_closed: SinnerEvent
    _distributed_system: Optional[DistributedProcessingSystem] = None

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
                'parameter': 'zmq-endpoint',
                'attribute': 'zmq_endpoint',
                'default': "tcp://127.0.0.1:5555",
                'help': 'ZeroMQ endpoint for the frame processor server'
            },
            {
                'parameter': 'server-mode',
                'attribute': 'server_mode',
                'choices': ["integrated", "subprocess", "external"],
                'default': "integrated",
                'help': 'Mode for running the processor server'
            },
            {
                'module_help': 'Distributed GUI Form'
            }
        ]

    def __init__(self, parameters: Namespace):
        """
        Initialize the distributed GUI form.

        Parameters:
        parameters (Namespace): Application parameters
        """
        if WINDOWS:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]

        self.parameters = parameters
        super().__init__(parameters)

        # Initialize distributed processing system
        self._initialize_distributed_system()

        #  Main window
        self.GUIWindow: CTk = CTk()  # the main window
        if self.geometry:
            self.GUIWindow.geometry(self.geometry)

        self.GUIWindow.iconbitmap(default=get_app_dir("sinner/gui/icons/sinner.ico"))
        self.GUIWindow.title('sinner distributed controls')
        self.GUIWindow.minsize(500, 130)
        self.GUIWindow.protocol('WM_DELETE_WINDOW', lambda: self.on_player_window_close())
        self._event_player_window_closed = SinnerEvent(on_set_callback=lambda: self.on_player_window_close())

        self.NavigationFrame: Frame = Frame(self.GUIWindow)  # Frame for navigation control and progressbar

        self.StatusBar = StatusBar(self.GUIWindow, borderwidth=1, relief=RIDGE, items={"Target resolution": "", "Render size": ""})

        # Create distributed GUI model
        self.create_gui_model()

        # Setup window event handlers
        self.GUIWindow.bind("<Configure>", lambda event: self.on_player_window_configure(event))
        self.GUIWindow.bind("<FocusIn>", lambda event: self.on_player_window_focus_in(event))
        self.GUIWindow.resizable(width=True, height=True)
        self.GUIWindow.bind("<KeyRelease>", lambda event: self.on_player_window_key_release(event))

        # Navigation slider
        self.NavigateSlider: BaseFramePosition = FrameSlider(self.NavigationFrame, from_=1, variable=self.GUIModel.position, command=lambda position: self.GUIModel.rewind(int(position)), progress=self.show_progress)

        # Controls frame and contents
        self.BaseFrame: Frame = Frame(self.GUIWindow)  # Frame for static controls with fixed size
        self.WidgetsFrame: Frame = Frame(self.GUIWindow)  # Frame for dynamic controls which can be hidden

        self.ButtonsFrame = Frame(self.BaseFrame)
        self.RunButton: Button = Button(self.ButtonsFrame, text="PLAY", width=10, command=lambda: self.on_run_button_press())

        self.ControlsFrame = Frame(self.BaseFrame)
        self.SubControlsFrame = Frame(self.ControlsFrame)

        self.QualityScaleLabel: Label = Label(self.SubControlsFrame, text="Quality scale:")
        self.QualityScaleSpinbox: Spinbox = Spinbox(self.SubControlsFrame, from_=1, to=100, increment=1, command=lambda: self.on_quality_scale_change(int(self.QualityScaleSpinbox.get())))
        self.QualityScaleSpinbox.bind('<KeyRelease>', lambda event: self.on_quality_scale_change(int(self.QualityScaleSpinbox.get())))
        self.QualityScaleSpinbox.set(self.GUIModel.quality)

        # Empty space to divide controls
        self.EmptyDivisor: Label = Label(self.SubControlsFrame)

        # Volume slider
        self.VolumeLabel: Label = Label(self.SubControlsFrame, text="Vol:")
        self.VolumeSlider: BaseFramePosition = SliderFramePosition(self.SubControlsFrame, from_=0, to=100, variable=self.GUIModel.volume, command=lambda position: self.GUIModel.set_volume(int(position)))

        # Source/target selection controls
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

        # Menus
        self.setup_menus()

    def _initialize_distributed_system(self) -> None:
        """Initialize the distributed processing system."""
        # Create the distributed system
        self._distributed_system = DistributedProcessingSystem(self.parameters)

    def create_gui_model(self) -> None:
        """Create and initialize the distributed GUI model."""
        # Create distributed GUI model
        self.GUIModel = create_distributed_gui_model(
            self.parameters,
            status_callback=lambda name, value: self.StatusBar.item(name, value),
            on_close_event=self._event_player_window_closed,
            progress_control=None  # Will be set after NavigateSlider is created
        )

    def setup_menus(self) -> None:
        """Setup application menus."""
        self.MainMenu: Menu = Menu(self.GUIWindow)

        # Operations submenu
        self.OperationsSubMenu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.OperationsSubMenu, label='Frame')  # type: ignore[no-untyped-call]
        self.OperationsSubMenu.add(COMMAND, label='Save as png', command=lambda: self.save_current_frame())  # type: ignore[no-untyped-call]
        self.OperationsSubMenu.add(COMMAND, label='Reprocess', command=lambda: self.GUIModel.update_preview(True))  # type: ignore[no-untyped-call]

        # Rotate submenu
        self.RotateModeVar: StringVar = StringVar(value="0°")
        self.RotateSubMenu: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.RotateSubMenu, label='Rotation')  # type: ignore[no-untyped-call]
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label="0°", command=lambda: self.set_rotate_mode(None))  # type: ignore[no-untyped-call]
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label="90°", command=lambda: self.set_rotate_mode(ROTATE_90_CLOCKWISE))  # type: ignore[no-untyped-call]
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label="180°", command=lambda: self.set_rotate_mode(ROTATE_180))  # type: ignore[no-untyped-call]
        self.RotateSubMenu.add(RADIOBUTTON, variable=self.RotateModeVar, label="270°", command=lambda: self.set_rotate_mode(ROTATE_90_COUNTERCLOCKWISE))  # type: ignore[no-untyped-call]

        # Sound submenu
        self.SoundEnabledVar: BooleanVar = BooleanVar(value=self.GUIModel.enable_sound())
        self.SoundSubMenu: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.SoundSubMenu, label='Sound')  # type: ignore[no-untyped-call]
        self.SoundSubMenu.add(CHECKBUTTON, variable=self.SoundEnabledVar, label='Enable sound', command=lambda: self.GUIModel.enable_sound(self.SoundEnabledVar.get()))  # type: ignore[no-untyped-call]
        self.SoundSubMenu.add(SEPARATOR)  # type: ignore[no-untyped-call]
        self.SoundSubMenu.add(COMMAND, label='Volume up', command=lambda: self.increase_volume())  # type: ignore[no-untyped-call]
        self.SoundSubMenu.add(COMMAND, label='Volume down', command=lambda: self.decrease_volume())  # type: ignore[no-untyped-call]

        # Audio backend submenu
        self.SoundSubMenu.add(SEPARATOR)  # type: ignore[no-untyped-call]
        self.AudioBackendVar: StringVar = StringVar(value=self.GUIModel.audio_backend)
        self.AudioBackendSelectionMenu: Menu = Menu(self.SoundSubMenu, tearoff=False)
        for available_backend in BaseAudioBackend.list():
            self.AudioBackendSelectionMenu.add(RADIOBUTTON, variable=self.AudioBackendVar, label=available_backend, command=lambda backend=available_backend: self.switch_audio_backend(backend))  # type: ignore[no-untyped-call]
        self.SoundSubMenu.add(CASCADE, menu=self.AudioBackendSelectionMenu, label='Audio backend')  # type: ignore[no-untyped-call]

        # Tools submenu
        self.StayOnTopVar: BooleanVar = BooleanVar(value=self.topmost)
        self.SourceLibraryVar: BooleanVar = BooleanVar(value=self.show_sources_library)
        self.ToolsSubMenu: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.ToolsSubMenu, label='Tools')  # type: ignore[no-untyped-call]
        self.ToolsSubMenu.add(CHECKBUTTON, label='Stay on top', variable=self.StayOnTopVar, command=lambda: self.set_topmost(self.StayOnTopVar.get()))  # type: ignore[no-untyped-call]

        # Library submenu
        self.LibraryMenu: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.LibraryMenu, label='Library')  # type: ignore[no-untyped-call]
        self.SourcesLibraryMenu: Menu = Menu(self.LibraryMenu, tearoff=False)
        self.TargetsLibraryMenu: Menu = Menu(self.LibraryMenu, tearoff=False)
        self.LibraryMenu.add(CASCADE, menu=self.SourcesLibraryMenu, label='Sources library')  # type: ignore[no-untyped-call]
        self.LibraryMenu.add(CASCADE, menu=self.TargetsLibraryMenu, label='Targets library')  # type: ignore[no-untyped-call]
        self.SourcesLibraryMenu.add(COMMAND, label='Add files', command=lambda: self.add_source_files())  # type: ignore[no-untyped-call]
        self.SourcesLibraryMenu.add(COMMAND, label='Add a folder', command=lambda: self.add_source_folder())  # type: ignore[no-untyped-call]
        self.SourcesLibraryMenu.add(SEPARATOR)  # type: ignore[no-untyped-call]
        self.SourcesLibraryMenu.add(COMMAND, label='Clear', command=lambda: self.source_clear())  # type: ignore[no-untyped-call]
        self.TargetsLibraryMenu.add(COMMAND, label='Add files', command=lambda: self.add_target_files())  # type: ignore[no-untyped-call]
        self.TargetsLibraryMenu.add(COMMAND, label='Add a folder', command=lambda: self.add_target_folder())  # type: ignore[no-untyped-call]
        self.TargetsLibraryMenu.add(SEPARATOR)  # type: ignore[no-untyped-call]
        self.TargetsLibraryMenu.add(COMMAND, label='Clear', command=lambda: self.target_clear())  # type: ignore[no-untyped-call]

        # Add distributed processing submenu
        self.DistributedMenu: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.DistributedMenu, label='Distributed')  # type: ignore[no-untyped-call]
        self.DistributedMenu.add(COMMAND, label='Server Status', command=lambda: self.show_server_status())  # type: ignore[no-untyped-call]
        self.DistributedMenu.add(COMMAND, label='Reconnect', command=lambda: self.reconnect_to_server())  # type: ignore[no-untyped-call]

        # Set menu
        self.GUIWindow.configure(menu=self.MainMenu, tearoff=False)

    # Event handlers
    def on_player_window_close(self) -> None:
        """Handle player window close event."""
        self.GUIModel.player_stop(wait=True)

        # Shutdown distributed system if enabled
        if self._distributed_system:
            self._distributed_system.shutdown()

        halt()

    def on_player_window_configure(self, event: Event) -> None:  # type: ignore[type-arg]
        """Handle window configure (resize/move) event."""
        if self.GUIWindow.wm_state() != 'zoomed':
            Config(self.parameters).set_key(self.__class__.__name__, 'controls-geometry', self.GUIWindow.geometry())
        Config(self.parameters).set_key(self.__class__.__name__, 'controls-state', self.GUIWindow.wm_state())

    def on_player_window_focus_in(self, event: Event) -> None:  # type: ignore[type-arg]
        """Handle window focus event."""
        if self.GUIModel:
            self.GUIModel.Player.bring_to_front()

    def on_player_window_key_release(self, event: Event) -> None:  # type: ignore[type-arg]
        """Handle key release events."""
        if event.keycode == 37:  # left arrow
            self.NavigateSlider.position = max(1, self.NavigateSlider.position - self.NavigateSlider.to // 100)
            self.GUIModel.rewind(self.NavigateSlider.position)
        if event.keycode == 39:  # right arrow
            self.GUIModel.rewind(self.NavigateSlider.position)
            self.NavigateSlider.position = min(self.NavigateSlider.to, self.NavigateSlider.position + self.NavigateSlider.to // 100)
        if event.keycode == 32:  # space bar
            self.on_run_button_press()

    def on_run_button_press(self) -> None:
        """Handle play/stop button press."""
        if self.GUIModel.player_is_started:
            self.GUIModel.player_stop()
            self.RunButton.configure(text="PLAY")
        else:
            self.GUIModel.player_start(start_frame=self.NavigateSlider.position)
            self.RunButton.configure(text="STOP")

    # UI layout
    def draw_controls(self) -> None:
        """Draw controls in the window."""
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

    # Utility methods
    def save_current_frame(self) -> None:
        """Save current frame to file."""
        save_file = filedialog.asksaveasfilename(title='Save frame', defaultextension='png')
        if save_file != '':
            self.GUIModel.Player.save_to_file(save_file)

    def set_rotate_mode(self, mode: int | None) -> None:
        """Set rotation mode for the player."""
        self.GUIModel.Player.rotate = mode

    def increase_volume(self) -> None:
        """Increase playback volume."""
        if self.GUIModel.volume.get() < 100:
            self.GUIModel.volume.set(self.GUIModel.volume.get() + 1)

    def decrease_volume(self) -> None:
        """Decrease playback volume."""
        if self.GUIModel.volume.get() > 0:
            self.GUIModel.volume.set(self.GUIModel.volume.get() - 1)

    def switch_audio_backend(self, backend: str) -> None:
        """Switch audio backend."""
        self.GUIModel.audio_backend = backend

    def format_target_info(self) -> str:
        """Format target resolution and framerate info."""
        return f"{self.GUIModel.frame_handler.resolution[0]}x{self.GUIModel.frame_handler.resolution[1]}@{round(self.GUIModel.frame_handler.fps, ndigits=3)}"

    def set_topmost(self, on_top: bool = True) -> None:
        """Set window to stay on top."""
        self.GUIWindow.wm_attributes("-topmost", on_top)
        self.GUIModel.Player.set_topmost(on_top)

    def show(self) -> CTk:
        """Show the GUI window and initialize components."""
        self.draw_controls()
        self.SourcePathEntry.set_text(self.GUIModel.source_path)
        self.TargetPathEntry.set_text(self.GUIModel.target_path)
        self.StatusBar.item('Target resolution', self.format_target_info())
        self.GUIModel.update_preview()
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
        """Load window geometry from settings."""
        self.GUIWindow.update()
        self.GUIWindow.update_idletasks()
        current_size_part, _ = self.GUIWindow.geometry().split('+', 1)
        current_height = int(current_size_part.split('x')[1])
        size_part, position_part = self.geometry.split('+', 1)
        requested_width = int(size_part.split('x')[0])
        self.GUIWindow.geometry(f"{requested_width}x{current_height}+{position_part}")

    # Source and target handling
    def change_source(self) -> bool:
        """Change source file through file dialog."""
        selected_file = self.SelectSourceDialog.askopenfilename(title='Select a source', initialdir=self.GUIModel.source_dir)
        if selected_file != '':
            self._set_source(selected_file)
            return True
        return False

    def _set_source(self, filename: str) -> None:
        """Set source file path."""
        self.GUIModel.source_path = filename
        self.SourcePathEntry.set_text(filename)

    def change_target(self) -> bool:
        """Change target file through file dialog."""
        selected_file = self.SelectTargetDialog.askopenfilename(title='Select a target', initialdir=self.GUIModel.target_dir)
        if selected_file != '':
            self._set_target(selected_file)
            return True
        return False

    def _set_target(self, filename: str) -> None:
        """Set target file path."""
        self.NavigateSlider.position = 1
        self.GUIModel.target_path = filename
        self.update_slider_bounds()
        self.TargetPathEntry.set_text(filename)
        self.on_quality_scale_change(self.GUIModel.quality)
        self.StatusBar.item('Target resolution', self.format_target_info())

    def update_slider_bounds(self) -> None:
        """Update navigation slider bounds based on frame count."""
        self.NavigateSlider.to = self.GUIModel.frame_handler.fc
        self.NavigateSlider.position = 1
        if self.NavigateSlider.to > 1:
            self.NavigateSlider.enable()
        else:
            self.NavigateSlider.disable()

    def on_quality_scale_change(self, frame_value: int) -> None:
        """Handle change in quality scale."""
        if frame_value > self.QualityScaleSpinbox.cget('to'):
            frame_value = self.QualityScaleSpinbox.cget('to')
        if frame_value < self.QualityScaleSpinbox.cget('from'):
            frame_value = self.QualityScaleSpinbox.cget('from')
        self.GUIModel.quality = frame_value
        if self.GUIModel.frame_handler.resolution:
            self.StatusBar.item('Render size', f"{self.GUIModel.quality}% ({int(self.GUIModel.frame_handler.resolution[0] * self.GUIModel.quality / 100)}x{int(self.GUIModel.frame_handler.resolution[1] * self.GUIModel.quality / 100)})")

    # Library handling
    def source_library_add(self, paths: List[str], reload: bool = False) -> None:
        """Add sources to the library."""
        if reload:
            self.SourcesLibrary.clear_thumbnails()

        for path in paths:
            if is_dir(path):
                for dir_file in get_directory_file_list(path, is_image):
                    self.SourcesLibrary.add_thumbnail(source_path=dir_file)
            else:
                self.SourcesLibrary.add_thumbnail(source_path=path)

    def add_source_files(self) -> None:
        """Add source files to the library."""
        image_extensions = get_type_extensions('image/')
        file_paths = filedialog.askopenfilenames(
            title="Select files to add to sources",
            filetypes=[('Image files', image_extensions), ('All files', '*.*')],
            initialdir=self.GUIModel.source_dir
        )
        if file_paths:
            self.source_library_add(paths=list(file_paths))

    def add_source_folder(self) -> None:
        """Add a folder of source files to the library."""
        directory = filedialog.askdirectory(
            title="Select a directory to add sources",
            initialdir=self.GUIModel.source_dir
        )
        if directory:
            self.source_library_add(paths=[directory])

    def source_clear(self) -> None:
        """Clear the sources library."""
        self.SourcesLibrary.clear_thumbnails()

    def target_library_add(self, paths: List[str], reload: bool = False) -> None:
        """Add targets to the library."""
        if reload:
            self.TargetsLibrary.clear_thumbnails()

        for path in paths:
            if is_dir(path):
                for dir_file in get_directory_file_list(path, is_video):
                    self.TargetsLibrary.add_thumbnail(source_path=dir_file)
            else:
                self.TargetsLibrary.add_thumbnail(source_path=path)

    def add_target_files(self) -> None:
        """Add target files to the library."""
        file_paths = filedialog.askopenfilenames(
            title="Select files to add to targets",
            filetypes=[('All files', '*.*')],
            initialdir=self.GUIModel.target_dir
        )
        if file_paths:
            self.target_library_add(paths=list(file_paths))

    def add_target_folder(self) -> None:
        """Add a folder of target files to the library."""
        directory = filedialog.askdirectory(
            title="Select a directory to add targets",
            initialdir=self.GUIModel.target_dir
        )
        if directory:
            self.target_library_add(paths=[directory])

    def target_clear(self) -> None:
        """Clear the targets library."""
        self.TargetsLibrary.clear_thumbnails()

    # Distributed-specific methods
    def show_server_status(self) -> None:
        """Show server status information."""
        if hasattr(self.GUIModel, "_processor_client"):
            client = getattr(self.GUIModel, "_processor_client")
            if client:
                status = client.get_server_status()
                if status:
                    processed_count = status.get("processed_count", 0)
                    processing_count = status.get("processing_count", 0)
                    processing_fps = status.get("processing_fps", 0.0)

                    # Format detailed status text
                    status_text = f"Server Status:\n" \
                                  f"Processed frames: {processed_count}\n" \
                                  f"Processing frames: {processing_count}\n" \
                                  f"Processing speed: {processing_fps:.2f} FPS"

                    # Update status bar with brief info
                    self.StatusBar.item("Server Status", f"Processed: {processed_count}, FPS: {processing_fps:.2f}")

                    # Show detailed status in a dialog
                    from tkinter import Toplevel, Label, Button

                    status_window = Toplevel(self.GUIWindow)
                    status_window.title("Distributed Processing Status")
                    status_window.geometry("300x150")
                    status_window.resizable(False, False)
                    status_window.transient(self.GUIWindow)
                    status_window.grab_set()

                    Label(status_window, text=status_text, justify='left', padx=20, pady=20).pack(expand=True)
                    Button(status_window, text="Close", command=status_window.destroy).pack(pady=10)

                    # Center window on parent
                    status_window.update_idletasks()
                    x = self.GUIWindow.winfo_rootx() + (self.GUIWindow.winfo_width() - status_window.winfo_width()) // 2
                    y = self.GUIWindow.winfo_rooty() + (self.GUIWindow.winfo_height() - status_window.winfo_height()) // 2
                    status_window.geometry(f"+{x}+{y}")
                else:
                    self.StatusBar.item("Server Status", "Failed to get server status")

    def reconnect_to_server(self) -> None:
        """Reconnect to the processing server."""
        if hasattr(self.GUIModel, "_processor_client"):
            client = getattr(self.GUIModel, "_processor_client")
            if client and hasattr(client, "reset_connection"):
                success = client.reset_connection()
                if success:
                    self.StatusBar.item("Server Connection", "Reconnected successfully")
                else:
                    self.StatusBar.item("Server Connection", "Reconnection failed")

    def shutdown(self) -> None:
        """Shutdown the distributed system."""
        if self._distributed_system:
            self._distributed_system.shutdown()
