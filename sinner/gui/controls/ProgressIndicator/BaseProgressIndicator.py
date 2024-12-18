# Base class for all progress indicators
from abc import abstractmethod, ABC
from typing import List, Any


class BaseProgressIndicator(ABC):
    @abstractmethod
    def set_segments(self, segments: int) -> None:
        """
        Изменяет количество сегментов и сбрасывает их состояния

        Args:
            segments: новое количество сегментов
        """

        pass

    @abstractmethod
    def update_states(self, states: List[int]) -> None:
        """Обновляет состояния сегментов и перерисовывает их"""
        pass

    @abstractmethod
    def set_segment_value(self, index: int, value: int) -> None:
        """
        Устанавливает значение для определенного сегмента

        Args:
            index: индекс сегмента (0-based)
            value: новое значение сегмента
        """
        pass

    @abstractmethod
    def set_segment_values(self, indexes: List[int], value: int, reset: bool = True, update: bool = True) -> None:
        """
        Устанавливает заданное значение для списка сегментов

        Args:
            indexes: список индексов сегментов
            value: значение для установки
            reset: если True, сначала сбрасывает все сегменты в начальное состояние (0)
            update: если True, обновить любые значения, иначе только пустые
        """
        pass

    @abstractmethod
    async def set_segment_value_async(self, index: int, value: int) -> None:
        """
        Асинхронно устанавливает значение сегмента

        Args:
            index: индекс сегмента (0-based)
            value: новое значение сегмента
        """
        pass

    @abstractmethod
    def place_configure(self, cnf={}, **kw) -> None:  # type: ignore[no-untyped-def]
        """
        Этот метод требует реализации только если она не предоставлена
        другим родительским классом
        """
        pass

    @property
    @abstractmethod
    def pass_through(self) -> Any:
        pass

    @pass_through.setter
    @abstractmethod
    def pass_through(self, value: Any) -> None:
        pass
