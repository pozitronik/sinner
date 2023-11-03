import threading
from typing import Callable

import cv2
import numpy
import pygame
from pygame import Surface

from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.helpers.FrameHelper import resize_proportionally
from sinner.typing import Frame
from sinner.utilities import get_app_dir


class PygameFramePlayer(BaseFramePlayer):
    screen: Surface = None
    width: int
    height: int
    caption: str

    _events_thread: threading.Thread
    _event_handlers: dict[int, Callable] = {}

    def __init__(self, width: int, height: int, caption: str = 'PlayerControl'):
        self.width = width
        self.height = height
        self.caption = caption
        pygame.init()
        self._events_thread = threading.Thread(target=self._handle_events, name="_handle_events")
        self._events_thread.daemon = True
        # self._events_thread.start()

    def add_handler(self, event_type: int, handler: Callable) -> None:
        self._event_handlers[event_type] = handler
        self._reload_event_handlers()

    def _reload_event_handlers(self):
        pygame.event.set_blocked(None)
        pygame.event.set_allowed([key for key in self._event_handlers])

    def show(self) -> None:
        if self.screen is None:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            pygame.display.set_caption(self.caption)
            pygame.display.set_icon(pygame.image.load(get_app_dir("sinner/gui/icons/sinner_64.png")))

    def hide(self) -> None:
        if self.screen is not None:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.HIDDEN)
        pygame.quit()

    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True) -> None:
        self.show()
        if frame is None and self._last_frame is not None:
            frame = self._last_frame
        if frame is not None:
            self._last_frame = frame

            frame = self._rotate_frame(frame)
            frame = numpy.flip((cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), 0)
            # note: now the frame has the flipped shape (WIDTH, HEIGHT)

            if resize is True:  # resize to the current canvas size
                frame = resize_proportionally(frame, (self.screen.get_width(), self.screen.get_height()))
            elif isinstance(resize, tuple):
                frame = resize_proportionally(frame, resize)
            elif resize is False:  # resize the canvas to the image size
                self.adjust_size(False)

        image_surface = pygame.surfarray.make_surface(frame)
        self.screen.blit(image_surface, ((self.screen.get_width() - frame.shape[0]) // 2, (self.screen.get_height() - frame.shape[1]) // 2))
        pygame.display.flip()

    def adjust_size(self, redraw: bool = True, size: tuple[int, int] | None = None) -> None:
        if size is not None or self._last_frame is not None:
            if size is None:
                size = self._last_frame.shape[1], self._last_frame.shape[0]
            # note: set_mode size parameter has the WIDTH, HEIGHT dimensions order
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
            # it is required to redraw the frame after resize, if it is not be intended after
            if redraw:
                self.show_frame()

    def clear(self) -> None:
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

    def _handle_events(self):
        self._reload_event_handlers()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type in self._event_handlers:
                    handler = self._event_handlers[event.type]
                    handler()

