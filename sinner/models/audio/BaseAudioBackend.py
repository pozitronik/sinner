import os
from abc import ABC, abstractmethod
from argparse import Namespace
from typing import Any

from sinner.Status import Status
from sinner.utilities import normalize_path, load_class


class BaseAudioBackend(Status, ABC):
    _media_path: str | None = None

    @staticmethod
    def create(backend_name: str, parameters: Namespace, media_path: str | None = None) -> 'BaseAudioBackend':  # audio backend factory
        backend_class = load_class(os.path.dirname(__file__), backend_name)

        if backend_class and issubclass(backend_class, BaseAudioBackend):
            params: dict[str, Any] = {'parameters': parameters, 'media_path': media_path}
            return backend_class(**params)
        else:
            raise ValueError(f"Invalid backend name: {backend_name}")

    @staticmethod
    def available() -> bool:
        """
        :return: True, if this backend is available
        """
        return True

    def __init__(self, parameters: Namespace, media_path: str | None = None) -> None:
        super().__init__(parameters)
        if media_path:
            self.media_path = media_path

    @property
    def media_path(self) -> str | None:
        """
        :return: string path to the current mediafile, if present
        """
        return self._media_path

    @media_path.setter
    def media_path(self, media_path: str) -> None:
        """
        The path to the mediafile
        :param media_path: string path to the current mediafile
        """
        self._media_path = str(normalize_path(media_path))
        self.update_status(f"Using audio backend for {self._media_path}")

    @property
    @abstractmethod
    def volume(self) -> int:
        """
        :return: the current volume level
        """
        pass

    @volume.setter
    @abstractmethod
    def volume(self, vol: int) -> None:
        """
        Sets the volume level
        :param vol: volume level (0 - 100)
        """
        pass

    @property
    @abstractmethod
    def position(self) -> int | None:
        """
        :return: the current playing position in seconds, if supported (else None)
        """
        pass

    @position.setter
    @abstractmethod
    def position(self, position: int) -> None:
        """
        Sets the current position, if seconds
        :param position: required position
        """
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
