import logging
import threading

import zmq
from typing import Optional, Callable

from zmq import Socket, ZMQError

from sinner.gui.server.api.BaseClientAPI import BaseClientAPI
from sinner.gui.server.api.messages.NotificationMessage import NotificationMessage
from sinner.gui.server.api.messages.RequestMessage import RequestMessage
from sinner.gui.server.api.messages.ResponseMessage import ResponseMessage


class ZMQClientAPI(BaseClientAPI):
    _sub_endpoint: str = "tcp://127.0.0.1:5556"  # Эндпоинт для подписки на нотификации
    _timeout: int = 5000
    _context: zmq.Context
    _req_socket: Socket
    _sub_socket: Optional[Socket] = None
    _logger: logging.Logger
    _lock: threading.Lock

    _notification_thread: Optional[threading.Thread] = None  # тред подписки на нотификации
    _notification_handler: Optional[Callable[[NotificationMessage], None]] = None  # Колбэк обработки нотификаций от сервера
    _notification_running: bool = False

    def __init__(self, notification_handler: Optional[Callable[[NotificationMessage], None]] = None, reply_endpoint: str = "tcp://127.0.0.1:5555", sub_endpoint: str = "tcp://127.0.0.1:5556", timeout: int = 5000):
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
                if self._sub_socket is None:
                    raise Exception("Subscription socket is not initialized")
                if self._sub_socket.poll(timeout=100):  # Ожидание 100мс
                    self._handle_notification(NotificationMessage.deserialize(self._sub_socket.recv()))
            except zmq.ZMQError as e:
                if e.errno != zmq.EAGAIN:  # Не таймаут
                    self._logger.error(f"Error receiving notification: {e}")
            except Exception as e:
                self._logger.error(f"Error processing notification: {e}")

    def _handle_notification(self, notification: NotificationMessage) -> None:
        if self._notification_handler is None:
            self._logger.error(f"No handler defined for notification: {notification.notification}")
        else:
            try:
                self._logger.debug(f"Handling notification: {notification}")
                self._notification_handler(notification)
            except Exception as e:
                self._logger.error(f"Error in notification callback: {e}")

    def send_request(self, request: RequestMessage) -> ResponseMessage:
        try:
            with self._lock:
                try:
                    self._req_socket.send(request.serialize())
                    return ResponseMessage.deserialize(self._req_socket.recv())
                except zmq.ZMQError as e:
                    if e.errno == zmq.EAGAIN:  # Timeout
                        self._logger.error(f"Timeout waiting for response when sending to {self._endpoint}: {e}")
                        # Восстанавливаем сокет после таймаута
                        self._recreate_socket()
                    else:
                        self._logger.error(f"ZMQ error {e} when sending to {self._endpoint}")
                        self._recreate_socket()
        except zmq.ZMQError as e:
            self._logger.error(f"ZMQ error sending request: {e}")
        except Exception as e:
            self._logger.error(f"Error sending request: {e}")
            self._logger.exception("Client request error")
        return ResponseMessage.error_response()

    def _recreate_socket(self) -> None:
        """Пересоздание REQ сокета после ошибки."""
        self._logger.info("Recreating REQ socket")
        if self._req_socket:
            self._req_socket.close(linger=0)  # linger=0 важно для немедленного закрытия

        self._req_socket = self._context.socket(zmq.REQ)
        self._req_socket.setsockopt(zmq.RCVTIMEO, self._timeout)
        self._req_socket.connect(self._endpoint)
