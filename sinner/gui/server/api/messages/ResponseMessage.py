from dataclasses import dataclass
from typing import Dict, Any, ClassVar, Optional, Type, TypeVar

from sinner.gui.server.api.messages.BaseMessage import BaseMessage

# Константы статусов
STATUS_OK: str = "ok"
STATUS_ERROR: str = "error"

T = TypeVar('T', bound='ResponseMessage')


@dataclass
class ResponseMessage(BaseMessage):
    """
    Класс для представления ответов сервера.
    Обязательно содержит поле status с типом статуса ответа.
    Может содержать дополнительное поле message и другие параметры.
    """
    # Константы доступны в классе
    STATUS_OK: ClassVar[str] = STATUS_OK
    STATUS_ERROR: ClassVar[str] = STATUS_ERROR

    def __init__(self, status: str = STATUS_OK, message: Optional[str] = None) -> None:
        """
        Инициализация ответа с указанием статуса и сообщения.

        Args:
            status: Статус ответа
            message: Сообщение ответа
        """
        super().__init__()
        if status:
            self.status = status
        if message:
            self.message = message

    @property
    def status(self) -> str:
        """Получение статуса ответа"""
        if hasattr(self, '_status'):
            return self._status
        else:
            raise ValueError("Field 'status' is required")

    @status.setter
    def status(self, value: str) -> None:
        """Установка статуса ответа"""
        self._status = value

    @property
    def message(self) -> Optional[str]:
        """Получение сообщения ответа"""
        return self._message if hasattr(self, '_message') else None

    @message.setter
    def message(self, value: str) -> None:
        """Установка сообщения ответа"""
        self._message = value

    def validate(self) -> None:
        """Валидация обязательных полей"""
        if not self.status:
            raise ValueError("Field 'status' is required")

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в обычный словарь"""
        result = {'status': self.status} if self.status else {}
        if self.message:
            result['message'] = self.message

        # Добавляем дополнительные поля
        result.update(self._extra_fields)
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Создание объекта из словаря"""
        status_value = data.get('status')
        message_value = data.get('message')

        if status_value is None:
            raise ValueError("Field 'status' is required")

        instance = cls(status=status_value, message=message_value)

        # Копируем данные без полей status и message
        data_copy = data.copy()
        if 'status' in data_copy:
            del data_copy['status']
        if 'message' in data_copy:
            del data_copy['message']

        # Обновляем дополнительные поля
        instance.update(data_copy)

        return instance

    @classmethod
    def ok_response(cls: Type[T], message: Optional[str] = None, **kwargs) -> T:  # type: ignore[no-untyped-def]
        """Создание успешного ответа"""
        instance = cls(status=STATUS_OK, message=message)

        # Добавляем дополнительные параметры
        for key, value in kwargs.items():
            instance[key] = value

        return instance

    @classmethod
    def error_response(cls: Type[T], message: Optional[str] = None, **kwargs) -> T:  # type: ignore[no-untyped-def]
        """Создание ответа с ошибкой"""
        instance = cls(status=STATUS_ERROR, message=message)

        # Добавляем дополнительные параметры
        for key, value in kwargs.items():
            instance[key] = value

        return instance

    def is_ok(self) -> bool:
        return self.status == STATUS_OK
