from abc import abstractmethod

from sinner.typing import Frame


class BasePlayer:
    _last_frame: Frame | None = None  # the last viewed frame

    @abstractmethod
    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True) -> None:
        pass

    @abstractmethod
    def adjust_size(self) -> None:
        pass
