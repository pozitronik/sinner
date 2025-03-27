from dataclasses import dataclass
from typing import Dict, Any, ClassVar, Type, TypeVar

from sinner.gui.server.api.messages.BaseMessage import BaseMessage

# Константы запросов: GET_* - получение данных, SET_* - установка данных, CMD_* - управляющая команда
GET_STATUS = "GET_STATUS"
GET_SOURCE = "GET_SOURCE"
SET_SOURCE = "SET_SOURCE"
GET_TARGET = "GET_TARGET"
SET_TARGET = "SET_TARGET"
GET_QUALITY = "GET_QUALITY"
SET_QUALITY = "SET_QUALITY"
GET_POSITION = "GET_POSITION"
SET_POSITION = "SET_POSITION"
GET_FRAME = "CMD_FRAME"  # запрос на получение бинарного необработанного кадра
GET_METADATA = "GET_METADATA"  # запрос метаданных цели
SET_SOURCE_FILE = "SET_SOURCE_FILE"  # Передача бинарного файла в источник
SET_TARGET_FILE = "SET_TARGET_FILE"  # Передача бинарного файла в цель
CMD_STOP_PROCESSING = "CMD_STOP_PROCESSING"
CMD_START_PROCESSING = "CMD_START_PROCESSING"
CMD_FRAME_PROCESSED = "CMD_FRAME_PROCESSED"  # запрос на генерацию кадра

T = TypeVar('T', bound='RequestMessage')


@dataclass
class RequestMessage(BaseMessage):
    """
    Класс для отправки запросов на сервер
    Обязательно содержит поле request с типом запроса.
    """

    # Константы доступны в классе
    GET_STATUS: ClassVar[str] = GET_STATUS
    GET_SOURCE: ClassVar[str] = GET_SOURCE
    SET_SOURCE: ClassVar[str] = SET_SOURCE
    GET_TARGET: ClassVar[str] = GET_TARGET
    SET_TARGET: ClassVar[str] = SET_TARGET
    GET_QUALITY: ClassVar[str] = GET_QUALITY
    SET_QUALITY: ClassVar[str] = SET_QUALITY
    GET_POSITION: ClassVar[str] = GET_POSITION
    SET_POSITION: ClassVar[str] = SET_POSITION
    CMD_START_PROCESSING: ClassVar[str] = CMD_START_PROCESSING
    CMD_STOP_PROCESSING: ClassVar[str] = CMD_STOP_PROCESSING
    CMD_FRAME_PROCESSED: ClassVar[str] = CMD_FRAME_PROCESSED
    GET_FRAME: ClassVar[str] = GET_FRAME
    GET_METADATA: ClassVar[str] = GET_METADATA
    SET_SOURCE_FILE: ClassVar[str] = SET_SOURCE_FILE
    SET_TARGET_FILE: ClassVar[str] = SET_TARGET_FILE

    def __init__(self, request: str) -> None:
        """
        Инициализация запроса с указанием типа запроса.

        Args:
            request: Тип запроса
        """
        super().__init__()
        if request:
            self.request = request

    @property
    def request(self) -> str:
        """Получение типа запроса"""
        if hasattr(self, '_request'):
            return self._request
        else:
            raise ValueError("Field 'request' is required")

    @request.setter
    def request(self, value: str) -> None:
        """Установка типа запроса"""
        self._request = value

    def validate(self) -> None:
        """Валидация обязательных полей"""
        if not self.request:
            raise ValueError("Field 'request' is required")

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в обычный словарь"""
        result = {'request': self.request} if self.request else {}
        # Добавляем дополнительные поля
        result.update(self._extra_fields)
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Создание объекта из словаря"""
        request_value = data.get('request')

        if request_value is None:
            raise ValueError("Field 'request' is required")

        instance = cls(request=request_value)

        # Копируем данные без поля request
        data_copy = data.copy()
        if 'request' in data_copy:
            del data_copy['request']

        # Обновляем дополнительные поля
        instance.update(data_copy)

        return instance

    @classmethod
    def create(cls: Type[T], request_type: str, **kwargs) -> T:  # type: ignore[no-untyped-def]
        """Создать запрос с параметрами"""
        instance = cls(request=request_type)

        # Добавляем дополнительные параметры
        for key, value in kwargs.items():
            instance[key] = value

        # Проверяем валидность созданного объекта
        instance.validate()
        return instance
