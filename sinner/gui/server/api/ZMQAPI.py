import json
import logging
import threading

import zmq
from typing import Dict, Any

from zmq import Socket, ZMQError

from sinner.gui.server.api.BaseAPI import BaseAPI, STATUS_OK


class ZMQAPI(BaseAPI):
    _timeout: int = 1000
    _context: zmq.Context
    _req_socket: Socket
    _logger: logging.Logger
    _lock: threading.Lock

    def __init__(self, endpoint: str = "tcp://127.0.0.1:5555", timeout: int = 1000):
        """
        Initialize ZeroMQ communication.

        Parameters:
        endpoint (str): ZeroMQ endpoint for communication
        """
        super().__init__(endpoint)
        self._timeout = timeout
        self._context = zmq.Context()
        self._req_socket = self._context.socket(zmq.REQ)
        self._req_socket.setsockopt(zmq.RCVTIMEO, self._timeout)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._lock = threading.Lock()

    def connect(self) -> bool:
        try:
            self._req_socket.connect(self._endpoint)
            return True
        except ZMQError:
            return False

    def disconnect(self) -> None:
        """Close ZeroMQ context and sockets."""
        if self._req_socket:
            self._req_socket.close()
        if self._context:
            self._context.term()

    def send_message(self, message: Dict[str, Any]) -> bool:
        try:
            with self._lock:
                try:
                    self._req_socket.send(self._serialize_message(message))
                    response = self._deserialize_message(self._req_socket.recv())
                    return response.get("status") == STATUS_OK
                except zmq.ZMQError as e:
                    if e.errno == zmq.EAGAIN:  # Timeout
                        self._logger.error(f"Timeout waiting for response when sending to {self._endpoint}: {e}")
                    else:
                        self._logger.error(f"ZMQ error {e} when sending to {self._endpoint}")
                    return False
        except zmq.ZMQError as e:
            self._logger.error(f"ZMQ error sending request: {e}")
        except Exception as e:
            self._logger.error(f"Error sending request: {e}")
            self._logger.exception("Client request error")
        return False

    def send_request(self, request: Dict[str, Any]) -> Any:
        try:
            with self._lock:
                try:
                    self._req_socket.send(self._serialize_message(request))
                    response = self._deserialize_message(self._req_socket.recv())
                    return response.get("status") == STATUS_OK
                except zmq.ZMQError as e:
                    if e.errno == zmq.EAGAIN:  # Timeout
                        self._logger.error(f"Timeout waiting for response when sending to {self._endpoint}: {e}")
                    else:
                        self._logger.error(f"ZMQ error {e} when sending to {self._endpoint}")
                    return False
        except zmq.ZMQError as e:
            self._logger.error(f"ZMQ error sending request: {e}")
        except Exception as e:
            self._logger.error(f"Error sending request: {e}")
            self._logger.exception("Client request error")
        return False

    @staticmethod
    def _serialize_message(message: Dict[str, Any]) -> bytes:
        """Serialize message to JSON and encode to bytes."""
        return json.dumps(message).encode()

    def _deserialize_message(self, message: bytes) -> Dict[str, Any]:
        """Deserialize message from bytes to JSON."""
        try:
            return json.loads(message.decode())
        except json.JSONDecodeError as e:
            self._logger.error(f"Failed to deserialize message: {e}")
            return {"status": "error", "message": "Invalid message format"}
