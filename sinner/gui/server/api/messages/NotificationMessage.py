from dataclasses import dataclass
from typing import Dict, Any, ClassVar, Type, TypeVar

from sinner.gui.server.api.messages.BaseMessage import BaseMessage

NTF_FRAME = "NTF_FRAME"  # оповещение о готовности фрейма

T = TypeVar('T', bound='NotificationMessage')


@dataclass
class NotificationMessage(BaseMessage):
    """
    Класс для отправки нотификаций клиенту
    Обязательно содержит поле notification с типом нотфикации
    """

    # Константы доступны в классе
    NTF_FRAME: ClassVar[str] = NTF_FRAME

    def __init__(self, notification: str) -> None:
        """
        Инициализация запроса с указанием типа запроса.

        Args:
            notification: Тип запроса
        """
        super().__init__()
        if notification:
            self.notification = notification

    @property
    def notification(self) -> str:
        """Получение типа запроса"""
        if hasattr(self, '_notification'):
            return self._notification
        else:
            raise ValueError("Field 'notification' is required")

    @notification.setter
    def notification(self, value: str) -> None:
        """Установка типа запроса"""
        self._notification = value

    def validate(self) -> None:
        """Валидация обязательных полей"""
        if not self.notification:
            raise ValueError("Field 'notification' is required")

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в обычный словарь"""
        result = {'notification': self.notification} if self.notification else {}
        # Добавляем дополнительные поля
        result.update(self._extra_fields)
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Создание объекта из словаря"""
        notification_value = data.get('notification')

        if notification_value is None:
            raise ValueError("Field 'notification' is required")

        instance = cls(notification=notification_value)

        # Копируем данные без поля notification
        data_copy = data.copy()
        if 'notification' in data_copy:
            del data_copy['notification']

        # Обновляем дополнительные поля
        instance.update(data_copy)

        return instance

    @classmethod
    def create(cls: Type[T], notification_type: str, **kwargs) -> T:  # type: ignore[no-untyped-def]  # todo: type **kwargs as dict[str, Any] or Any everywhere
        """Создать запрос с параметрами"""
        instance = cls(notification=notification_type)

        # Добавляем дополнительные параметры
        for key, value in kwargs.items():
            instance[key] = value

        # Проверяем валидность созданного объекта
        instance.validate()
        return instance
