from abc import ABC, abstractmethod

from sinner.typing import NumeratedFrame


class BaseFrameBuffer(ABC):

    @abstractmethod
    def pop(self) -> NumeratedFrame | None:
        """
        :return: a frame from the buffer or None, if the buffer is empty
        """
        pass

    @abstractmethod
    def push(self, frame: NumeratedFrame) -> int:
        """
        Adds a frame to the buffer
        :param frame: a new frame
        :return: the current buffer frames count
        """
        pass

    @property
    @abstractmethod
    def len(self) -> int:
        """
        :return: the current buffer frames count
        """
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        """
        :return: summary size of all frames in the buffer
        """
        pass