# Base class for all progress indicators
from abc import abstractmethod
from typing import List


class BaseProgressIndicator:
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

    def set_segment_values(self, indexes: List[int], value: int, reset: bool = True) -> None:
        """
        Устанавливает заданное значение для списка сегментов

        Args:
            indexes: список индексов сегментов
            value: значение для установки
            reset: если True, сначала сбрасывает все сегменты в начальное состояние (0)
        """
        pass

    async def set_segment_value_async(self, index: int, value: int) -> None:
        """
        Асинхронно устанавливает значение сегмента

        Args:
            index: индекс сегмента (0-based)
            value: новое значение сегмента
        """
        pass