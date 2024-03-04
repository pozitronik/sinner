from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.typing import Frame


class NullFramePlayer(BaseFramePlayer):

    def set_fullscreen(self, fullscreen: bool = True) -> None:
        pass

    def set_topmost(self, on_top: bool = True) -> None:
        pass

    def bring_to_front(self) -> None:
        pass

    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True, rotate: bool = True) -> None:
        pass

    def adjust_size(self, redraw: bool = True, size: tuple[int, int] | None = None) -> None:
        pass

    def clear(self) -> None:
        pass
