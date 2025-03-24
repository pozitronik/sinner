from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Type
import json

T = TypeVar('T', bound='BaseMessage')


class BaseMessage(ABC):
    """
    Абстрактный базовый класс для представления сообщений обмена между клиентом и сервером.
    """

    def __init__(self) -> None:
        """Инициализация базового класса"""
        self._extra_fields: Dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """Доступ к дополнительным полям через атрибуты"""
        if name in self._extra_fields:
            return self._extra_fields[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Установка значений как атрибутов класса или дополнительных полей"""
        # Служебные поля устанавливаем напрямую
        if name.startswith('_') or hasattr(type(self), name) and isinstance(getattr(type(self), name), property):
            super().__setattr__(name, value)
        else:
            # Проверяем, есть ли атрибут в классе
            try:
                super().__getattribute__(name)
                # Если атрибут есть, устанавливаем его
                super().__setattr__(name, value)
            except AttributeError:
                # Если атрибута нет, добавляем в extra_fields
                self._extra_fields[name] = value

    def __getitem__(self, key: str) -> Any:
        """Поддержка доступа по ключу (как в словаре)"""
        # Сначала проверяем атрибуты класса
        try:
            return getattr(self, key)
        except AttributeError:
            # Затем проверяем extra_fields
            return self._extra_fields.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Поддержка установки значения по ключу"""
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Метод get как у словаря"""
        try:
            return getattr(self, key)
        except AttributeError:
            return self._extra_fields.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        """Обновление полей из словаря"""
        for key, value in data.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в обычный словарь"""
        # Метод должен быть переопределен в подклассах
        result = {}
        # Добавляем extra_fields
        result.update(self._extra_fields)
        return result

    def to_json(self) -> str:
        """Сериализация в JSON строку"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Создание объекта из словаря"""
        # Метод должен быть переопределен в подклассах
        instance = cls()
        instance.update(data)
        return instance

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Создание объекта из JSON строки"""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
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

    @abstractmethod
    def validate(self) -> None:
        """
        Метод для валидации обязательных полей.
        Должен быть реализован в подклассах.
        """
        pass
