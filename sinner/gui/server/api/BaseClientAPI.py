from abc import ABC, abstractmethod
from typing import Optional

from sinner.gui.server.api.messages.RequestMessage import RequestMessage
from sinner.gui.server.api.messages.ResponseMessage import ResponseMessage


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
    def send_request(self, request: RequestMessage) -> Optional[ResponseMessage]:
        """Sends a request to the endpoint and returns the response when it is ready. Returns None on Error"""
        pass
