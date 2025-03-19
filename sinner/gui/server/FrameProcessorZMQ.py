import json
import logging
from typing import Dict, Any

import zmq


class FrameProcessorZMQ:  # todo: API model interface
    """Base class for ZeroMQ communication for the frame processor system."""

    def __init__(self, endpoint: str = "tcp://127.0.0.1:5555"):
        """
        Initialize ZeroMQ communication.

        Parameters:
        endpoint (str): ZeroMQ endpoint for communication
        """
        self.endpoint = endpoint
        self.context = zmq.Context()
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _serialize_message(message: Dict[str, Any]) -> bytes:
        """Serialize message to JSON and encode to bytes."""
        return json.dumps(message).encode()

    def _deserialize_message(self, message: bytes) -> Dict[str, Any]:
        """Deserialize message from bytes to JSON."""
        try:
            return json.loads(message.decode())
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to deserialize message: {e}")
            return {"status": "error", "message": "Invalid message format"}

    @staticmethod
    def build_response(status: str, **kwargs) -> Dict[str, Any]:
        """Build a response message."""
        response = {"status": status}
        response.update(kwargs)
        return response

    def close(self) -> None:
        """Close ZeroMQ context and sockets."""
        if hasattr(self, 'socket'):
            self.socket.close()
        if hasattr(self, 'context'):
            self.context.term()
