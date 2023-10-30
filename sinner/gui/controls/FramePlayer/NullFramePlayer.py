from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.typing import Frame


class NullFramePlayer(BaseFramePlayer):

    def __init__(self, **kwargs):
        pass

    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True) -> None:
        pass

    def adjust_size(self) -> None:
        pass
