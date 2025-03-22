import asyncio
import json
import logging
import platform
from typing import Dict, Any, Callable, Optional, TypeAlias

import zmq.asyncio
from zmq import ZMQError
from zmq.asyncio import Socket as AsyncSocket

from sinner.gui.server.api.BaseAPI import STATUS_ERROR

MessageData: TypeAlias = Dict[str, Any]


class ZMQREPPUBAPI:
    _timeout: int = 1000
    _reply_endpoint: str = "tcp://127.0.0.1:5555"
    _context: zmq.asyncio.Context
    _reply_socket: AsyncSocket  # the listening socket
    _publish_endpoint: str = "tcp://127.0.0.1:5556"
    _publish_socket: zmq.Socket  # the publishing socket

    _logger: logging.Logger
    _server_running: bool = False
    _request_handler: Optional[Callable[[MessageData], MessageData]] = None  # external method to handle incoming messages

    def __init__(self, handler: Optional[Callable[[MessageData], MessageData]] = None, reply_endpoint: str = "tcp://127.0.0.1:5555", publish_endpoint: str = "tcp://127.0.0.1:5556", timeout: int = 1000):
        if platform.system().lower() == 'windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._request_handler = handler
        self._timeout = timeout
        self._reply_endpoint = reply_endpoint
        self._context = zmq.asyncio.Context()
        self._reply_socket = self._context.socket(zmq.REP)
        # self._reply_socket.setsockopt(zmq.RCVTIMEO, self._timeout)  # Асинхронный ZMQ сам управляет ожиданием через asyncio.

        self._publish_endpoint = publish_endpoint
        self._publish_socket = self._context.socket(zmq.PUB)
        self._publish_socket.setsockopt(zmq.RCVTIMEO, self._timeout)

        self._logger = logging.getLogger(self.__class__.__name__)

    async def bind(self) -> bool:
        try:
            self._reply_socket.bind(self._reply_endpoint)
            self._publish_socket.bind(self._publish_endpoint)

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
        if self._reply_socket:
            self._reply_socket.close()
        if self._publish_socket:
            self._publish_socket.close()
        if self._context:
            self._context.term()

        self._server_running = False

    async def _message_handler(self) -> None:
        """Async message handler that responds to requests."""
        while self._server_running:
            try:
                # Асинхронно ждем сообщения - НЕ блокирует поток!
                message_data = await self._reply_socket.recv()
                message = self._deserialize_message(message_data)

                self._logger.info(f"Received message: {message}")
                response = self._handle_request(message)

                # Асинхронно отправляем ответ
                await self._reply_socket.send(self._serialize_message(response))
            except zmq.ZMQError as e:
                if e.errno == zmq.EAGAIN:  # Тайм-аут
                    self._logger.error(f"Timeout handling message: {e}")
                    await asyncio.sleep(0.01)
                else:
                    self._logger.error(f"ZMQ error in message handler: {e}")
            except Exception as e:
                self._logger.error(f"Error handling message: {e}")
                # Пауза при ошибке, чтобы не загружать процессор
                await asyncio.sleep(0.1)

    def notify(self, notification: MessageData) -> None:
        try:
            self._publish_socket.send(self._serialize_message(notification), zmq.NOBLOCK)
        except Exception as e:
            self._logger.error(f"Failed to send notification: {e}")

    def _handle_request(self, message: MessageData) -> MessageData:
        if self._request_handler is None:
            return self.build_response(STATUS_ERROR, message=f"Handler is not defined")
        else:
            return self._request_handler(message)

    @staticmethod
    def build_response(status: str, **kwargs) -> MessageData:
        """Build a response message."""
        response = {"status": status}
        response.update(kwargs)
        return response

    @staticmethod
    def _serialize_message(message: MessageData) -> bytes:
        """Serialize message to JSON and encode to bytes."""
        return json.dumps(message).encode()

    def _deserialize_message(self, message: bytes) -> MessageData:
        """Deserialize message from bytes to JSON."""
        try:
            return json.loads(message.decode())
        except json.JSONDecodeError as e:
            self._logger.error(f"Failed to deserialize message: {e}")
            return {"status": "error", "message": "Invalid message format"}
