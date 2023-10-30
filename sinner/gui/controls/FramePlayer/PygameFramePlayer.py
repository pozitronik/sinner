import cv2
import numpy
import pygame
from pygame import Surface

from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.helpers.FrameHelper import resize_proportionally
from sinner.typing import Frame


class PygameFramePlayer(BaseFramePlayer):
    screen: Surface = None

    def __init__(self, width: int, height: int, caption: str = '😈'):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(caption)

    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True) -> None:
        if frame is None and self._last_frame is not None:
            frame = self._last_frame
        if frame is not None:
            self._last_frame = frame
            if resize is True:  # resize to the current canvas size
                frame = resize_proportionally(frame, (self.screen.get_height(), self.screen.get_width()))
            elif isinstance(resize, tuple):
                frame = resize_proportionally(frame, resize)
            elif resize is False:  # resize the canvas to the image size
                self.adjust_size()

        frame = numpy.flip(numpy.rot90((cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))), 0)

        image_surface = pygame.surfarray.make_surface(frame)
        self.screen.blit(image_surface, (0, 0))
        pygame.display.flip()

    def adjust_size(self) -> None:
        if self._last_frame is not None:
            # note: set_mode size parameter has the WIDTH, HEIGHT dimensions order
            self.screen = pygame.display.set_mode((self._last_frame.shape[1], self._last_frame.shape[0]))
