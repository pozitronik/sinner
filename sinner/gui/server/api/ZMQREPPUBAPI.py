import asyncio
import json
import logging
import platform
from typing import Dict, Any, Callable, Optional

import zmq.asyncio
from zmq import ZMQError

from sinner.gui.server.api.BaseAPI import STATUS_ERROR


class ZMQREPPUBAPI:
    _timeout: int = 1000
    _rep_endpoint: str = "tcp://127.0.0.1:5555"
    _rep_context: zmq.asyncio.Context
    _rep_socket: zmq.Socket  # the listening socket
    _pub_endpoint: str = "tcp://127.0.0.1:5556"
    _pub_context: zmq.asyncio.Context
    _pub_socket: zmq.Socket  # the publishing socket

    _logger: logging.Logger
    _server_running: bool = False
    _request_handler: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None  # external method to handle incoming messages

    def __init__(self, handler: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None, rep_endpoint: str = "tcp://127.0.0.1:5555", pub_endpoint: str = "tcp://127.0.0.1:5556", timeout: int = 1000):
        if platform.system().lower() == 'windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._request_handler = handler
        self._timeout = timeout
        self._rep_endpoint = rep_endpoint
        self._rep_context = zmq.asyncio.Context()
        self._rep_socket = self._rep_context.socket(zmq.REP)
        self._rep_socket.setsockopt(zmq.RCVTIMEO, self._timeout)

        self._pub_endpoint = pub_endpoint
        self._pub_context = zmq.Context.instance()
        self._pub_socket = self._pub_context.socket(zmq.PUB)
        self._pub_socket.setsockopt(zmq.RCVTIMEO, self._timeout)

        self._logger = logging.getLogger(self.__class__.__name__)

    async def connect(self) -> bool:
        try:
            self._rep_socket.bind(self._rep_endpoint)
            self._pub_socket.connect(self._pub_endpoint)

            self._server_running = True
            self._logger.info("Frame processor server started")

            await asyncio.gather(
                self._message_handler()
            )
            return True
        except ZMQError:
            return False

    def disconnect(self) -> None:
        """Close ZeroMQ context and sockets."""
        if self._rep_socket:
            self._rep_socket.close()
        if self._rep_context:
            self._rep_context.term()
        if self._pub_socket:
            self._pub_socket.close()
        if self._pub_context:
            self._pub_context.term()

        self._server_running = False

    async def _message_handler(self) -> None:
        """Async message handler that responds to requests."""
        while self._server_running:
            try:
                # Асинхронно ждем сообщения - НЕ блокирует поток!
                message_data = await self._rep_socket.recv()
                message = self._deserialize_message(message_data)

                self._logger.info(f"Received message: {message}")
                response = self._handle_request(message)

                # Асинхронно отправляем ответ
                await self._rep_socket.send(self._serialize_message(response))

            except Exception as e:
                self._logger.error(f"Error handling message: {e}")

    def notify(self, notification: Dict[str, Any]) -> None:
        try:
            self._pub_socket.send(self._serialize_message(notification), zmq.NOBLOCK)
        except Exception as e:
            self._logger.error(f"Failed to send notification: {e}")

    def _handle_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if self._request_handler is None:
            return self.build_response(STATUS_ERROR, message=f"Handler is not defined")
        else:
            return self._request_handler(message)

    @staticmethod
    def build_response(status: str, **kwargs) -> Dict[str, Any]:
        """Build a response message."""
        response = {"status": status}
        response.update(kwargs)
        return response

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
