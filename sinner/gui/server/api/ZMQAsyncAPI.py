import asyncio
import json
import logging
import platform
from typing import Dict, Any, Callable, Optional, TypeAlias, Coroutine

import zmq.asyncio
from zmq import ZMQError
from zmq.asyncio import Socket as AsyncSocket

from sinner.gui.server.api.BaseAPI import BaseAPI, STATUS_OK

MessageData: TypeAlias = Dict[str, Any]


class ZMQAsyncAPI(BaseAPI):
    _timeout: int = 1000
    _context: zmq.asyncio.Context
    _req_socket: AsyncSocket
    _sub_socket: Optional[AsyncSocket] = None
    _logger: logging.Logger

    _notification_running: bool = False
    _notification_task: Optional[asyncio.Task] = None
    _notification_callback: Optional[Callable[[MessageData], Coroutine[Any, Any, None]]] = None
    _sub_endpoint: str = "tcp://127.0.0.1:5556"

    def __init__(self, endpoint: str = "tcp://127.0.0.1:5555", sub_endpoint: str = "tcp://127.0.0.1:5556", timeout: int = 1000):
        """
        Initialize asynchronous ZeroMQ communication.

        Parameters:
        endpoint (str): ZeroMQ endpoint for REQ/REP communication
        sub_endpoint (str): ZeroMQ endpoint for SUB/PUB notifications
        timeout (int): Socket timeout in milliseconds
        """
        super().__init__(endpoint)

        # Для Windows нужна специальная политика событийного цикла
        if platform.system().lower() == 'windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._timeout = timeout
        self._sub_endpoint = sub_endpoint
        self._context = zmq.asyncio.Context()
        self._req_socket = self._context.socket(zmq.REQ)
        self._req_socket.setsockopt(zmq.RCVTIMEO, self._timeout)
        self._logger = logging.getLogger(self.__class__.__name__)

    async def connect(self) -> bool:
        """Connect the REQ socket to the server."""
        try:
            self._req_socket.connect(self._endpoint)
            self._logger.info(f"Connected to {self._endpoint}")
            return True
        except ZMQError as e:
            self._logger.error(f"Failed to connect REQ socket: {e}")
            return False

    async def disconnect(self) -> None:
        """Close ZeroMQ context and sockets."""
        await self.stop_notification_listener()

        if self._req_socket:
            self._req_socket.close()
        if self._sub_socket:
            self._sub_socket.close()
        if self._context:
            self._context.term()

        self._logger.info("Disconnected ZMQ sockets")

    # Методы для работы с нотификациями

    def set_notification_callback(self, callback: Callable[[MessageData], Coroutine[Any, Any, None]]) -> None:
        """
        Set async callback function for handling incoming notifications.

        Parameters:
        callback (callable): Async function that takes notification dict as parameter
        """
        self._notification_callback = callback
        self._logger.debug("Notification callback set")

    async def start_notification_listener(self) -> bool:
        """Start listening for notifications asynchronously."""
        if not self._sub_socket:
            self._sub_socket = self._context.socket(zmq.SUB)
            # Подписываемся на все сообщения (пустая строка - нет фильтрации)
            self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        try:
            self._sub_socket.connect(self._sub_endpoint)
            self._notification_running = True

            # Запускаем асинхронную задачу для получения нотификаций
            self._notification_task = asyncio.create_task(self._notification_listener())
            self._logger.info(f"Started notification listener on {self._sub_endpoint}")
            return True
        except ZMQError as e:
            self._logger.error(f"Failed to start notification listener: {e}")
            if self._sub_socket:
                self._sub_socket.close()
                self._sub_socket = None
            return False

    async def stop_notification_listener(self) -> None:
        """Stop the notification listener task."""
        self._notification_running = False
        if self._notification_task:
            try:
                # Даём задаче время на корректное завершение
                await asyncio.wait_for(self._notification_task, timeout=1.0)
            except asyncio.TimeoutError:
                # Если задача не завершается, отменяем её
                self._notification_task.cancel()
                try:
                    await self._notification_task
                except asyncio.CancelledError:
                    pass
            self._notification_task = None

        if self._sub_socket:
            self._sub_socket.close()
            self._sub_socket = None

        self._logger.info("Notification listener stopped")

    async def _notification_listener(self) -> None:
        """Asynchronous task to receive notifications."""
        while self._notification_running:
            try:
                # Ждём нотификации
                message_data = await self._sub_socket.recv()
                notification = self._deserialize_message(message_data)

                self._logger.debug(f"Received notification: {notification}")

                # Вызов асинхронного колбэка
                if self._notification_callback:
                    try:
                        await self._notification_callback(notification)
                    except Exception as e:
                        self._logger.error(f"Error in notification callback: {e}")
            except ZMQError as e:
                if e.errno != zmq.EAGAIN:  # Не таймаут
                    self._logger.error(f"Error receiving notification: {e}")
                await asyncio.sleep(0.01)  # Небольшая пауза при ошибке
            except asyncio.CancelledError:
                # Корректно обрабатываем отмену задачи
                self._logger.info("Notification listener task cancelled")
                break
            except Exception as e:
                self._logger.error(f"Error processing notification: {e}")
                await asyncio.sleep(0.1)  # Пауза при неожиданной ошибке

    # Методы отправки запросов

    async def send_message(self, message: MessageData) -> bool:
        """
        Send a message to the server and check for success status.

        Parameters:
        message (dict): Message to send

        Returns:
        bool: True if server responded with success status
        """
        try:
            await self._req_socket.send(self._serialize_message(message))
            response_data = await self._req_socket.recv()
            response = self._deserialize_message(response_data)
            return response.get("status") == STATUS_OK
        except ZMQError as e:
            if e.errno == zmq.EAGAIN:  # Timeout
                self._logger.error(f"Timeout waiting for response when sending to {self._endpoint}: {e}")
            else:
                self._logger.error(f"ZMQ error {e} when sending to {self._endpoint}")
            return False
        except Exception as e:
            self._logger.error(f"Error sending message: {e}")
            return False

    async def send_request(self, request: MessageData) -> Any:
        """
        Send a request and get the response data.

        Parameters:
        request (dict): Request to send

        Returns:
        Any: Response data if successful, False otherwise
        """
        try:
            await self._req_socket.send(self._serialize_message(request))
            response_data = await self._req_socket.recv()
            response = self._deserialize_message(response_data)

            if response.get("status") == STATUS_OK:
                return response.get("response")
            return False
        except ZMQError as e:
            if e.errno == zmq.EAGAIN:  # Timeout
                self._logger.error(f"Timeout waiting for response: {e}")
            else:
                self._logger.error(f"ZMQ error: {e}")
            return False
        except Exception as e:
            self._logger.error(f"Error sending request: {e}")
            return False

    # Синхронные обертки для совместимости с существующим кодом

    def connect_sync(self) -> bool:
        """Synchronous wrapper for connect method."""
        return asyncio.run(self.connect())

    def disconnect_sync(self) -> None:
        """Synchronous wrapper for disconnect method."""
        asyncio.run(self.disconnect())

    def send_message_sync(self, message: MessageData) -> bool:
        """Synchronous wrapper for send_message method."""
        return asyncio.run(self.send_message(message))

    def send_request_sync(self, request: MessageData) -> Any:
        """Synchronous wrapper for send_request method."""
        return asyncio.run(self.send_request(request))

    # Вспомогательные методы

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

    # Пример использования синхронной обертки для запуска асинхронного кода

    def start_notification_listener_sync(self, callback=None) -> bool:
        """
        Start notification listener synchronously.

        This is a synchronous wrapper that allows starting the async notification
        listener from synchronous code.

        Parameters:
        callback (callable): Optional callback to set before starting

        Returns:
        bool: True if listener started successfully
        """
        # Настраиваем колбэк, если передан
        if callback:
            # Для синхронной обертки нужно создать асинхронный wrapper callback
            async def async_callback_wrapper(notification):
                callback(notification)

            self.set_notification_callback(async_callback_wrapper)

        # Создаем и запускаем event loop для запуска асинхронного кода
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Запускаем задачу и сохраняем ссылку на event loop
        self._async_loop = loop
        return loop.run_until_complete(self.start_notification_listener())
