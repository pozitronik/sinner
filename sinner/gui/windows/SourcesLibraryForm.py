from tkinter import Misc, NSEW, Menu, filedialog, CASCADE, COMMAND
from typing import List, Callable

from customtkinter import CTkToplevel

from sinner.gui.controls.ThumbnailWidget import ThumbnailWidget
from sinner.utilities import is_image, is_dir, get_directory_file_list, get_type_extensions


class SourcesLibraryForm:
    SourcesLibraryWnd: CTkToplevel
    SourcesLibrary: ThumbnailWidget
    _library: List[str] = []
    _library_is_loaded: bool = False
    _on_thumbnail_click_callback: Callable[[str], None] | None = None
    _on_window_close_callback: Callable[[], None] | None = None

    def __init__(self, master: Misc, library: List[str], on_thumbnail_click_callback: Callable[[str], None] | None = None, on_window_close_callback: Callable[[], None] | None = None):
        self.SourcesLibraryWnd = CTkToplevel(master)
        self.SourcesLibraryWnd.withdraw()  # hide window
        self.SourcesLibraryWnd.title('Sources library')
        self.SourcesLibrary = ThumbnailWidget(self.SourcesLibraryWnd)
        self.SourcesLibrary.grid(row=0, column=0, sticky=NSEW)
        self.SourcesLibraryWnd.grid_rowconfigure(0, weight=1)
        self.SourcesLibraryWnd.grid_columnconfigure(0, weight=1)

        self.SourcesLibraryWnd.protocol('WM_DELETE_WINDOW', lambda: self.hide())

        self._library = library
        self._on_thumbnail_click_callback = on_thumbnail_click_callback
        self._on_window_close_callback = on_window_close_callback

        self.MainMenu: Menu = Menu(self.SourcesLibraryWnd)
        self.Library: Menu = Menu(self.MainMenu, tearoff=False)
        self.MainMenu.add(CASCADE, menu=self.Library, label='Library')
        self.Library.add(COMMAND, label='Add files', command=lambda: self.add_files())
        self.Library.add(COMMAND, label='Add a folder', command=lambda: self.add_folder())

        self.SourcesLibraryWnd.configure(menu=self.MainMenu, tearoff=False)

    def show(self, show: bool = True) -> None:
        if show is True:
            self.SourcesLibraryWnd.deiconify()
            if not self._library_is_loaded:
                self.load(self._library)
                self._library_is_loaded = True
        else:
            self.SourcesLibraryWnd.withdraw()

    def hide(self) -> None:
        self.show(False)
        if self._on_window_close_callback:
            self._on_window_close_callback()

    def set_topmost(self, on_top: bool = True) -> None:
        self.SourcesLibraryWnd.wm_attributes("-topmost", on_top)

    def load(self, library: List[str] | None = None, callback: Callable[[str], None] | None = None, reload: bool = False) -> None:
        if library is None:
            library = self._library
        if callback is None:
            callback = self._on_thumbnail_click_callback
        if reload:
            self.SourcesLibrary.clear_thumbnails()
        for item in library:
            if is_image(item):
                self.SourcesLibrary.add_thumbnail(image_path=item, click_callback=lambda path: callback(path))
            elif is_dir(item):
                for dir_file in get_directory_file_list(item, is_image):
                    self.SourcesLibrary.add_thumbnail(image_path=dir_file, click_callback=lambda path: callback(path))

    def add_files(self) -> None:
        image_extensions = get_type_extensions('image/')
        file_paths = filedialog.askopenfilenames(
            title="Select files to add",
            filetypes=[('Image files', image_extensions), ('All files', '*.*')],
            initialdir="/",  # Set the initial directory (you can change this)
        )
        if file_paths:
            self.load(list(file_paths))

    def add_folder(self) -> None:
        directory = filedialog.askdirectory(
            title="Select a directory to add",
            initialdir="/",
        )
        if directory:
            self.load([directory])
