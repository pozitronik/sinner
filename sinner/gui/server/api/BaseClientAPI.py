from abc import ABC, abstractmethod
from typing import Any

from sinner.gui.server.api.messages.RequestMessage import RequestMessage


class BaseClientAPI(ABC):
    _endpoint: str

    def __init__(self, endpoint: str):
        self._endpoint = endpoint

    @abstractmethod
    def connect(self) -> bool:
        """Creates connection to endpoint"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection"""
        pass

    @abstractmethod
    def send_request(self, request: RequestMessage) -> Any:
        """Sends a request to the endpoint and returns the response"""
        pass
