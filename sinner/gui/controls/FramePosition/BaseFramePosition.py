from abc import abstractmethod
from typing import Any


class BaseFramePosition:

    @abstractmethod
    def pack(self, **kwargs) -> Any:
        pass

    @property
    @abstractmethod
    def position(self) -> int:
        pass

    @position.setter
    @abstractmethod
    def position(self, value: int) -> None:
        pass

    @property
    @abstractmethod
    def to(self) -> int:
        pass

    @to.setter
    @abstractmethod
    def to(self, value: int) -> None:
        pass

    @abstractmethod
    def set(self, output_value: int, from_variable_callback: bool = False) -> None:
        pass

    @abstractmethod
    def disable(self) -> None:
        pass

    @abstractmethod
    def enable(self) -> None:
        pass
