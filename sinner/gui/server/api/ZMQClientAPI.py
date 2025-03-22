import json
import logging
import threading

import zmq
from typing import Any, Optional, Callable

from zmq import Socket, ZMQError

from sinner.gui.server.api.APITypes import MessageData, STATUS_OK
from sinner.gui.server.api.BaseClientAPI import BaseClientAPI


class ZMQClientAPI(BaseClientAPI):
    _sub_endpoint: str = "tcp://127.0.0.1:5556"  # Эндпоинт для подписки на нотификации
    _timeout: int = 5000
    _context: zmq.Context
    _req_socket: Socket
    _sub_socket: Optional[Socket] = None
    _logger: logging.Logger
    _lock: threading.Lock

    _notification_thread: Optional[threading.Thread] = None  # тред подписки на нотификации
    _notification_handler: Optional[Callable[[MessageData], None]] = None  # Колбэк обработки нотификаций от сервера
    _notification_running: bool = False

    def __init__(self, notification_handler: Optional[Callable[[MessageData], MessageData]] = None, reply_endpoint: str = "tcp://127.0.0.1:5555", sub_endpoint: str = "tcp://127.0.0.1:5556", timeout: int = 5000):
        """
        Initialize ZeroMQ communication.

        Parameters:
        rep_endpoint (str): ZeroMQ endpoint for REQ/REP communication
        sub_endpoint (str): ZeroMQ endpoint for SUB/PUB notifications
        timeout (int): Socket timeout in milliseconds
        """
        super().__init__(reply_endpoint)
        self._notification_handler = notification_handler
        self._timeout = timeout
        self._sub_endpoint = sub_endpoint
        self._context = zmq.Context()
        self._req_socket = self._context.socket(zmq.REQ)
        self._req_socket.setsockopt(zmq.RCVTIMEO, self._timeout)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._lock = threading.Lock()

    def connect(self) -> bool:
        try:
            self._req_socket.connect(self._endpoint)
            self.start_notification_listener()
            return True
        except ZMQError as e:
            self._logger.error(f"Failed to connect REQ socket: {e}")
            return False

    def disconnect(self) -> None:
        """Close ZeroMQ context and sockets."""
        self.stop_notification_listener()  # Останавливаем прием нотификаций

        if self._req_socket:
            self._req_socket.close()
        if self._sub_socket:
            self._sub_socket.close()
        if self._context:
            self._context.term()

    def start_notification_listener(self) -> bool:
        """Start listening for notifications in background thread."""
        # Создаем SUB сокет если еще не создан
        if not self._sub_socket:
            self._sub_socket = self._context.socket(zmq.SUB)
            # Подписываемся на все сообщения (пустая строка - нет фильтрации)
            self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        try:
            # Подключаемся к PUB сокету сервера
            self._sub_socket.connect(self._sub_endpoint)

            # Запускаем фоновый поток для получения нотификаций
            self._notification_running = True
            self._notification_thread = threading.Thread(target=self._notification_listener, daemon=True)
            self._notification_thread.start()
            self._logger.info(f"Started notification listener on {self._sub_endpoint}")
            return True
        except ZMQError as e:
            self._logger.error(f"Failed to start notification listener: {e}")
            if self._sub_socket:
                self._sub_socket.close()
                self._sub_socket = None
            return False

    def stop_notification_listener(self) -> None:
        """Stop the notification listener thread."""
        self._notification_running = False
        if self._notification_thread and self._notification_thread.is_alive():
            self._notification_thread.join(timeout=1.0)
        if self._sub_socket:
            self._sub_socket.close()
            self._sub_socket = None

    def _notification_listener(self) -> None:
        """Background thread function to receive notifications."""
        while self._notification_running:
            try:
                # Неблокирующий прием с коротким таймаутом для возможности выхода из цикла
                if self._sub_socket.poll(timeout=100):  # Ожидание 100мс
                    self._handle_notification(self._deserialize_message(self._sub_socket.recv()))
            except zmq.ZMQError as e:
                if e.errno != zmq.EAGAIN:  # Не таймаут
                    self._logger.error(f"Error receiving notification: {e}")
            except Exception as e:
                self._logger.error(f"Error processing notification: {e}")

    def _handle_notification(self, notification: MessageData) -> None:
        if self._notification_handler is None:
            self._logger.error(f"No handler defined for notification: {notification}")
        else:
            try:
                self._notification_handler(notification)
            except Exception as e:
                self._logger.error(f"Error in notification callback: {e}")

    def send_message(self, message: MessageData) -> bool:
        try:
            with self._lock:
                try:
                    self._req_socket.send(self._serialize_message(message))
                    response = self._deserialize_message(self._req_socket.recv())
                    return response.get("status") == STATUS_OK
                except zmq.ZMQError as e:
                    if e.errno == zmq.EAGAIN:  # Timeout
                        self._logger.error(f"Timeout waiting for response when sending to {self._endpoint}: {e}")
                        # Восстанавливаем сокет после таймаута
                        self._recreate_socket()
                    else:
                        self._logger.error(f"ZMQ error {e} when sending to {self._endpoint}")
                        self._recreate_socket()
                    return False
        except zmq.ZMQError as e:
            self._logger.error(f"ZMQ error sending request: {e}")
        except Exception as e:
            self._logger.error(f"Error sending request: {e}")
            self._logger.exception("Client request error")
        return False

    def _recreate_socket(self) -> None:
        """Пересоздание REQ сокета после ошибки."""
        self._logger.info("Recreating REQ socket")
        if self._req_socket:
            self._req_socket.close(linger=0)  # linger=0 важно для немедленного закрытия

        self._req_socket = self._context.socket(zmq.REQ)
        self._req_socket.setsockopt(zmq.RCVTIMEO, self._timeout)
        self._req_socket.connect(self._endpoint)

    def send_request(self, request: MessageData) -> Any:
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
    def _serialize_message(message: MessageData) -> bytes:  # todo: вынести MessageData в dataclass
        """Serialize message to JSON and encode to bytes."""
        return json.dumps(message).encode()

    def _deserialize_message(self, message: bytes) -> MessageData:
        """Deserialize message from bytes to JSON."""
        try:
            return json.loads(message.decode())
        except json.JSONDecodeError as e:
            self._logger.error(f"Failed to deserialize message: {e}")
            return {"status": "error", "message": "Invalid message format"}
