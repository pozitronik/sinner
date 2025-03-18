import json
import logging
from typing import Dict, Any, List

import zmq


class FrameProcessorZMQ:
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

    def parse_frame_list(self, message: Dict[str, Any]) -> List[int]:
        """Extract frame indices list from message."""
        if "processed_frames" in message and isinstance(message["processed_frames"], list):
            return message["processed_frames"]
        return []

    def build_process_request(self, frame_index: int) -> Dict[str, Any]:
        """Build a process request message."""
        return {"action": "process", "frame_index": frame_index}

    def build_status_request(self) -> Dict[str, Any]:
        """Build a status request message."""
        return {"action": "status"}

    def build_list_processed_request(self) -> Dict[str, Any]:
        """Build a request to list processed frames."""
        return {"action": "list_processed"}

    @staticmethod
    def build_response(self, status: str, **kwargs) -> Dict[str, Any]:
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
