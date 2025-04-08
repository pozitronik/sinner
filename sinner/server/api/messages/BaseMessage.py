from abc import ABC
from typing import Dict, Any, TypeVar, Type
import json

T = TypeVar('T', bound='BaseMessage')


class BaseMessage(ABC):
    """
    Абстрактный базовый класс для представления сообщений обмена между клиентом и сервером.
    """

    def __init__(self, type_: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Инициализация базового класса"""
        self._type: str = type_
        self._fields: Dict[str, Any] = kwargs

    def __getattr__(self, name: str) -> Any:
        """Доступ к дополнительным полям через атрибуты"""
        if name in self._fields:
            return self._fields[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Установка значений как атрибутов класса или дополнительных полей"""
        # Служебные поля устанавливаем напрямую
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._fields[name] = value

    def __getitem__(self, key: str) -> Any:
        """Поддержка доступа по ключу (как в словаре)"""
        return self._fields.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Поддержка установки значения по ключу"""
        setattr(self, key, value)

    @property
    def type(self) -> str:
        return self._type

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в обычный словарь"""
        result = self._fields.copy()
        result['type'] = self._type
        return result

    def to_json(self) -> str:
        """Сериализация в JSON строку"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Создание объекта из JSON строки"""
        try:
            data: Dict[str, Any] = json.loads(json_str)
            type_ = data.pop('type', None)
            if type_ is None:
                raise TypeError("Type is not defined in JSON message")
            return cls(type_=type_, **data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    def serialize(self) -> bytes:
        """Сериализация в байты для передачи через ZMQ"""
        return self.to_json().encode()

    @classmethod
    def deserialize(cls: Type[T], message: bytes) -> T:
        """Десериализация из байтов, полученных через ZMQ"""
        try:
            return cls.from_json(message.decode())
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid message encoding: {e}")
