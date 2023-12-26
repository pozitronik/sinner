import ctypes
import threading
from typing import Callable

import cv2
import numpy
import pygame
from psutil import WINDOWS
from pygame import Surface

from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer, HWND_NOTOPMOST, HWND_TOPMOST, SWP_NOMOVE, SWP_NOSIZE, HWND_TOP, RotateMode
from sinner.helpers.FrameHelper import resize_proportionally
from sinner.typing import Frame
from sinner.utilities import get_app_dir


class PygameFramePlayer(BaseFramePlayer):
    screen: Surface
    width: int
    height: int
    caption: str

    _visible: bool = False
    _events_thread: threading.Thread
    _event_handlers: dict[int, Callable[[], None]] = {}

    def __init__(self, width: int, height: int, caption: str = 'PlayerControl'):
        self.width = width
        self.height = height
        self.caption = caption
        pygame.init()
        self._events_thread = threading.Thread(target=self._handle_events, name="_handle_events")
        self._events_thread.daemon = True
        # self._events_thread.start()

    def add_handler(self, event_type: int, handler: Callable[[], None]) -> None:
        self._event_handlers[event_type] = handler
        self._reload_event_handlers()

    def _reload_event_handlers(self) -> None:
        pygame.event.set_blocked(None)
        pygame.event.set_allowed([key for key in self._event_handlers])

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
            if rotate:
                frame = self._rotate_frame(frame, self.rotate.next())
            else:
                frame = self._rotate_frame(frame, rotate_mode=RotateMode.ROTATE_90)  # need to bring together numpy/pygame coordinates
            frame = numpy.flip((cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), 0)
            # note: now the frame has the flipped shape (WIDTH, HEIGHT)

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

    def _handle_events(self) -> None:
        self._reload_event_handlers()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type in self._event_handlers:
                    handler = self._event_handlers[event.type]
                    handler()

    def set_fullscreen(self, fullscreen: bool = True) -> None:
        pygame.display.toggle_fullscreen()

    def set_topmost(self, on_top: bool = True) -> None:
        if WINDOWS:
            # by some unknown reason it has no effect
            ctypes.windll.user32.SetWindowPos(pygame.display.get_wm_info()['window'], HWND_TOPMOST if on_top else HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)  # type: ignore[attr-defined]  # platform issue

    def bring_to_front(self) -> None:
        if WINDOWS:
            ctypes.windll.user32.SetWindowPos(pygame.display.get_wm_info()['window'], HWND_TOP, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)  # type: ignore[attr-defined]  # platform issue


"""

    def geometry(self, geometry_string: str | None = None) -> str | None:
        # mostly taken from customtkinter but ignores DPI scaling
        if geometry_string is not None:
            # update width and height attributes
            self.width, self.height, self., self.y = self._parse_geometry_string(geometry_string)
        else:
            return f"{round(self.width)}x{round(self.height)}+{self.x}+{self.y}"

    @staticmethod
    def _parse_geometry_string(geometry_string: str) -> tuple:  # taken from customtkinter
        #                 index:   1                   2           3          4             5       6
        # regex group structure: ('<width>x<height>', '<width>', '<height>', '+-<x>+-<y>', '-<x>', '-<y>')
        result = re.search(r"((\d+)x(\d+)){0,1}(\+{0,1}([+-]{0,1}\d+)\+{0,1}([+-]{0,1}\d+)){0,1}", geometry_string)

        width = int(result.group(2)) if result.group(2) is not None else None
        height = int(result.group(3)) if result.group(3) is not None else None
        x = int(result.group(5)) if result.group(5) is not None else None
        y = int(result.group(6)) if result.group(6) is not None else None

        return width, height, x, y

"""
