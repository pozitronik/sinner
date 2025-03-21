from abc import ABC, abstractmethod
from typing import Dict, Any

STATUS_OK: str = "ok"
STATUS_ERROR: str = "error"


class BaseAPI(ABC):
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
    def send_message(self, message: Dict[str, Any]) -> bool:
        """Sends a message to the endpoint and awaits the response"""
        pass

    @abstractmethod
    def send_request(self, request: Dict[str, Any]) -> Any:
        """Sends a request to the endpoint and returns the response"""
        pass

    @staticmethod
    def build_response(status: str = STATUS_OK, **kwargs) -> Dict[str, Any]:
        """Build a response message."""
        response = {"status": status}
        response.update(kwargs)
        return response
