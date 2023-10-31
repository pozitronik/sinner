import cv2
import numpy
import pygame
from pygame import Surface

from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.helpers.FrameHelper import resize_proportionally
from sinner.typing import Frame


class PygameFramePlayer(BaseFramePlayer):
    screen: Surface = None
    width: int
    height: int
    caption: str

    def __init__(self, width: int, height: int, caption: str = '😈'):
        self.width = width
        self.height = height
        self.caption = caption

    def show(self) -> None:
        if self.screen is None:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            pygame.display.set_caption(self.caption)

    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True) -> None:
        self.show()
        if frame is None and self._last_frame is not None:
            frame = self._last_frame
        if frame is not None:
            self._last_frame = frame
            if resize is True:  # resize to the current canvas size
                frame = resize_proportionally(frame, (self.screen.get_height(), self.screen.get_width()))
            elif isinstance(resize, tuple):
                frame = resize_proportionally(frame, resize)
            elif resize is False:  # resize the canvas to the image size
                self.adjust_size(False)

        frame = numpy.flip(numpy.rot90((cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))), 0)
        # note: now the frame has the flipped shape (WIDTH, HEIGHT)

        image_surface = pygame.surfarray.make_surface(frame)
        self.screen.blit(image_surface, ((self.screen.get_width() - frame.shape[0]) // 2, (self.screen.get_height() - frame.shape[1]) // 2))
        pygame.display.flip()

    def adjust_size(self, redraw: bool = True) -> None:
        if self._last_frame is not None:
            # note: set_mode size parameter has the WIDTH, HEIGHT dimensions order
            self.screen = pygame.display.set_mode((self._last_frame.shape[1], self._last_frame.shape[0]), pygame.RESIZABLE)
            # it is required to redraw the frame after resize, if it is not be intended after
            if redraw:
                self.show_frame()

    def clear(self) -> None:
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
