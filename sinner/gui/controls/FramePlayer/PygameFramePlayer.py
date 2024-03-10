import ctypes
import threading
from ctypes import wintypes
from time import sleep
from typing import Callable

import pygame
from psutil import WINDOWS
from pygame import Surface

from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer, HWND_NOTOPMOST, HWND_TOPMOST, SWP_NOMOVE, SWP_NOSIZE, HWND_TOP, RotateMode, SWP_NOACTIVATE
from sinner.helpers.FrameHelper import resize_proportionally
from sinner.models.Event import Event
from sinner.typing import Frame
from sinner.utilities import get_app_dir
from pygame.event import Event as PygameEvent


class PygameFramePlayer(BaseFramePlayer):
    screen: Surface
    width: int
    height: int
    caption: str
    on_close_event: Event | None

    _visible: bool = False
    _events_thread: threading.Thread
    _event_handlers: dict[int, Callable[[PygameEvent], None]] = {}
    _event_processing: Event  # the flag to control start/stop event_handling thread

    def __init__(self, width: int, height: int, caption: str = 'PlayerControl', on_close_event: Event | None = None):
        self.width = width
        self.height = height
        self.caption = caption
        self.on_close_event = on_close_event
        pygame.init()
        self._event_processing: Event = Event()
        self._events_thread = threading.Thread(target=self._handle_events, name="_handle_events")
        self._events_thread.daemon = True
        self._events_thread.start()

        self.add_handler(pygame.QUIT, lambda event: self._event_processing.clear())
        self.add_handler(pygame.WINDOWRESIZED, lambda event: self.show_frame())
        self.add_handler(pygame.WINDOWCLOSE, lambda event: self.close())

        self._event_processing.set()

    def close(self) -> None:
        self._event_processing.clear()  # stop handlers
        # self.screen = None
        pygame.quit()
        if self.on_close_event:
            self.on_close_event.set()

    def add_handler(self, event_type: int, handler: Callable[[PygameEvent], None]) -> None:
        self._event_handlers[event_type] = handler
        self._reload_event_handlers()

    def _reload_event_handlers(self) -> None:
        pygame.event.set_blocked(None)
        pygame.event.set_allowed([key for key in self._event_handlers])

    def _handle_events(self) -> None:
        self._reload_event_handlers()
        while self._event_processing.is_set():
            for event in pygame.event.get():
                if event.type in self._event_handlers:
                    handler = self._event_handlers[event.type]
                    handler(event)
            sleep(0.01)  # should prevent a high CPU load

    def show(self) -> None:
        if not self._visible:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            pygame.display.set_caption(self.caption)
            pygame.display.set_icon(pygame.image.load(get_app_dir("sinner/gui/icons/sinner_64.png")))
            self._visible = True
            self.bring_to_front()

    def hide(self) -> None:
        if self.screen is not None:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.HIDDEN)
        self._visible = False

    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True, rotate: bool = True) -> None:
        self.show()
        if frame is None and self._last_frame is not None:
            frame = self._last_frame
        if frame is not None:
            self._last_frame = frame
            frame = frame[::-1, :, [2, 1, 0]]  # swaps colors channels from BGR to RGB, flips the frame to a pygame coordinates

            if rotate:
                frame = self._rotate_frame(frame, self.rotate.prev())
            else:
                frame = self._rotate_frame(frame, rotate_mode=RotateMode.ROTATE_270)  # need to bring together numpy/pygame coordinates

            if resize is True:  # resize to the current player size
                frame = resize_proportionally(frame, (self.screen.get_width(), self.screen.get_height()))
            elif isinstance(resize, tuple):
                frame = resize_proportionally(frame, resize)
            elif resize is False:  # resize the player to the image size
                self.adjust_size(redraw=False)

            image_surface = pygame.surfarray.make_surface(frame)
            self.screen.blit(image_surface, ((self.screen.get_width() - frame.shape[0]) // 2, (self.screen.get_height() - frame.shape[1]) // 2))
            pygame.display.flip()

    def adjust_size(self, redraw: bool = True, size: tuple[int, int] | None = None) -> None:
        if size is None:
            if self._last_frame is not None:
                size = self._last_frame.shape[1], self._last_frame.shape[0]
        if size is not None:
            # note: set_mode size parameter has the WIDTH, HEIGHT dimensions order
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
            # it is required to redraw the frame after resize, if it is not be intended after
            if redraw:
                self.show_frame()

    def clear(self) -> None:
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

    def set_fullscreen(self, fullscreen: bool = True) -> None:
        pygame.display.toggle_fullscreen()

    def set_topmost(self, on_top: bool = True) -> None:
        if WINDOWS:
            if 'window' in pygame.display.get_wm_info():
                user32 = ctypes.WinDLL("user32")  # type: ignore[attr-defined]  # platform issue
                user32.SetWindowPos.restype = wintypes.HWND
                user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.UINT]
                user32.SetWindowPos(pygame.display.get_wm_info()['window'], HWND_TOPMOST if on_top else HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)

    def bring_to_front(self) -> None:
        if WINDOWS:
            if 'window' in pygame.display.get_wm_info():
                user32 = ctypes.WinDLL("user32")  # type: ignore[attr-defined]  # platform issue
                user32.SetWindowPos.restype = wintypes.HWND
                user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.UINT]
                user32.SetWindowPos(pygame.display.get_wm_info()['window'], HWND_TOP, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
