from typing import ClassVar, TypeVar

from sinner.server.api.messages.BaseMessage import BaseMessage

T = TypeVar('T', bound='RequestMessage')


class RequestMessage(BaseMessage):
    """
    Класс для отправки запросов на сервер
    """

    # Константы запросов: GET_* - получение данных, SET_* - установка данных, CMD_* - управляющая команда
    GET_STATUS: ClassVar[str] = "GET_STATUS"
    GET_SOURCE: ClassVar[str] = "GET_SOURCE"
    SET_SOURCE: ClassVar[str] = "SET_SOURCE"
    GET_TARGET: ClassVar[str] = "GET_TARGET"
    SET_TARGET: ClassVar[str] = "SET_TARGET"
    GET_QUALITY: ClassVar[str] = "GET_QUALITY"
    SET_QUALITY: ClassVar[str] = "SET_QUALITY"
    GET_POSITION: ClassVar[str] = "GET_POSITION"
    SET_POSITION: ClassVar[str] = "SET_POSITION"
    GET_PREPARE_FRAMES: ClassVar[str] = "GET_PREPARE_FRAMES"
    SET_PREPARE_FRAMES: ClassVar[str] = "SET_PREPARE_FRAMES"
    GET_FRAME: ClassVar[str] = "GET_FRAME"  # запрос на получение бинарного необработанного кадра
    GET_METADATA: ClassVar[str] = "GET_METADATA"  # запрос метаданных цели
    SET_SOURCE_FILE: ClassVar[str] = "SET_SOURCE_FILE"  # Передача бинарного файла в источник
    SET_TARGET_FILE: ClassVar[str] = "SET_TARGET_FILE"  # Передача бинарного файла в цель

    CMD_START_PROCESSING: ClassVar[str] = "CMD_START_PROCESSING"
    CMD_STOP_PROCESSING: ClassVar[str] = "CMD_STOP_PROCESSING"
    CMD_FRAME_PROCESSED: ClassVar[str] = "CMD_FRAME_PROCESSED"  # запрос на генерацию кадра
