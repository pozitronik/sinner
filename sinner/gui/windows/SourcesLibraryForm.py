from argparse import Namespace
from threading import Thread
from tkinter import Misc, NSEW, Menu, filedialog, CASCADE, COMMAND, SEPARATOR, Event
from typing import List, Callable

from customtkinter import CTkToplevel

from sinner.gui.controls.ThumbnailWidget import ThumbnailWidget
from sinner.models.Config import Config
from sinner.utilities import is_image, is_dir, get_directory_file_list, get_type_extensions
from sinner.validators.AttributeLoader import AttributeLoader, Rules


class SourcesLibraryForm(AttributeLoader):
    parameters: Namespace
    SourcesLibraryWnd: CTkToplevel
    SourcesLibrary: ThumbnailWidget
    _library: List[str] = []
    _library_is_loaded: bool = False
    _on_thumbnail_click_callback: Callable[[str], None] | None = None
    _on_window_close_callback: Callable[[], None] | None = None

    geometry: str
    state: str  # currently ignored, see issue #100

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'sources-library-geometry'},
                'attribute': 'geometry',
                'help': 'Window size and position'
            },
            {
                'parameter': {'sources-library-state'},
                'attribute': 'state',
            },
        ]

    def __init__(self, parameters: Namespace, master: Misc, library: List[str], on_thumbnail_click_callback: Callable[[str], None] | None = None, on_window_close_callback: Callable[[], None] | None = None):
        self.parameters = parameters
        super().__init__(parameters)
        self.SourcesLibraryWnd = CTkToplevel(master)
        if self.geometry:
            self.SourcesLibraryWnd.geometry(self.geometry)
        # if self.state:
        #     self.SourcesLibraryWnd.wm_state(self.state)
        self.SourcesLibraryWnd.withdraw()  # hide window
        self.SourcesLibraryWnd.title('Sources library')
        self.SourcesLibrary = ThumbnailWidget(self.SourcesLibraryWnd, temp_dir=vars(self.parameters).get('temp_dir'))
        self.SourcesLibrary.grid(row=0, column=0, sticky=NSEW)
        self.SourcesLibraryWnd.grid_rowconfigure(0, weight=1)
        self.SourcesLibraryWnd.grid_columnconfigure(0, weight=1)

        self.SourcesLibraryWnd.protocol('WM_DELETE_WINDOW', lambda: self.hide())

        self._library = library
        self._on_thumbnail_click_callback = on_thumbnail_click_callback
        self._on_window_close_callback = on_window_close_callback

        self.MainMenu: Menu = Menu(self.SourcesLibraryWnd)
        self.Library: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.Library, label='Library')  # type: ignore[no-untyped-call]  # it is a library method
        self.Library.add(COMMAND, label='Add files', command=lambda: self.add_files())  # type: ignore[no-untyped-call]  # it is a library method
        self.Library.add(COMMAND, label='Add a folder', command=lambda: self.add_folder())  # type: ignore[no-untyped-call]  # it is a library method
        self.Library.add(SEPARATOR)  # type: ignore[no-untyped-call]  # it is a library method
        self.Library.add(COMMAND, label='Clear', command=lambda: self.clear())  # type: ignore[no-untyped-call]  # it is a library method

        self.SourcesLibraryWnd.configure(menu=self.MainMenu, tearoff=False)
        self.SourcesLibraryWnd.bind("<Configure>", lambda event: on_player_window_configure(event))

        # noinspection PyUnusedLocal
        def on_player_window_configure(event: Event) -> None:  # type: ignore[type-arg]
            if self.SourcesLibraryWnd.wm_state() != 'zoomed':
                Config(self.parameters).set_key(self.__class__.__name__, 'sources-library-geometry', self.SourcesLibraryWnd.geometry())
            Config(self.parameters).set_key(self.__class__.__name__, 'sources-library-state', self.SourcesLibraryWnd.wm_state())

    def show(self, show: bool = True) -> None:
        if show is True:
            self.SourcesLibraryWnd.deiconify()
            if not self._library_is_loaded:
                self.add(self._library)
                self._library_is_loaded = True
        else:
            self.SourcesLibraryWnd.withdraw()

    def hide(self) -> None:
        self.show(False)
        if self._on_window_close_callback:
            self._on_window_close_callback()

    def set_topmost(self, on_top: bool = True) -> None:
        self.SourcesLibraryWnd.wm_attributes("-topmost", on_top)

    def add(self, library: List[str] | None = None, callback: Callable[[str], None] | None = None, reload: bool = False) -> None:
        if library is None:
            library = self._library
        if callback is None:
            callback = self._on_thumbnail_click_callback
        if reload:
            self.SourcesLibrary.clear_thumbnails()

        def add_image(image_path: str) -> None:
            if is_image(image_path):
                self.SourcesLibrary.add_thumbnail(image_path=image_path, click_callback=lambda path: callback(path))  # type: ignore[misc]  # callback is always defined

        for item in library:
            if is_image(item):
                # Start a new thread for each image
                Thread(target=add_image, args=(item,)).start()
            elif is_dir(item):
                for dir_file in get_directory_file_list(item, is_image):
                    Thread(target=add_image, args=(dir_file,)).start()

    def add_files(self) -> None:
        image_extensions = get_type_extensions('image/')
        file_paths = filedialog.askopenfilenames(
            title="Select files to add",
            filetypes=[('Image files', image_extensions), ('All files', '*.*')],
            initialdir="/",  # Set the initial directory (you can change this)
        )
        if file_paths:
            self.add(list(file_paths))

    def add_folder(self) -> None:
        directory = filedialog.askdirectory(
            title="Select a directory to add",
            initialdir="/",
        )
        if directory:
            self.add([directory])

    def clear(self) -> None:
        self.SourcesLibrary.clear_thumbnails()
