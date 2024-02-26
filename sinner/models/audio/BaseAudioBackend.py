from abc import ABC, abstractmethod
from argparse import Namespace

from sinner.Status import Status
from sinner.utilities import normalize_path


class BaseAudioBackend(Status, ABC):
    _media_path: str | None = None

    @staticmethod
    def available() -> bool:
        """
        If this backend is available
        """
        return True

    def __init__(self, parameters: Namespace, media_path: str | None = None) -> None:
        super().__init__(parameters)
        if media_path:
            self.media_path = media_path

    @property
    def media_path(self) -> str | None:
        return self._media_path

    @media_path.setter
    def media_path(self, media_path: str) -> None:
        self._media_path = str(normalize_path(media_path))
        self.update_status(f"Using audio backend for {self._media_path}")

    @property
    @abstractmethod
    def volume(self) -> int:
        pass

    @volume.setter
    @abstractmethod
    def volume(self, vol: int) -> None:
        pass

    @property
    @abstractmethod
    def position(self) -> int | None:
        """
        Returns the current playing position in seconds, if supported (else None)
        """
        pass

    @position.setter
    @abstractmethod
    def position(self, position: int) -> None:
        pass

    @abstractmethod
    def play(self) -> None:
        pass

    @abstractmethod
    def pause(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def unpause(self) -> None:
        pass
