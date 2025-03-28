from typing import Dict, Any, ClassVar, Optional, Type, TypeVar

from sinner.gui.server.api.messages.BaseMessage import BaseMessage

T = TypeVar('T', bound='ResponseMessage')


class ResponseMessage(BaseMessage):
    """
    Класс для представления ответов сервера.
    Обязательно содержит поле status с типом статуса ответа.
    Может содержать дополнительное поле message и другие параметры.
    """
    # Константы статусов
    STATUS_OK: ClassVar[str] = "ok"
    STATUS_ERROR: ClassVar[str] = "error"

    # Константы типов ответов
    GENERAL: ClassVar[str] = "GENERAL"  # Общий тип ответа, содержит только статус
    METADATA: ClassVar[str] = "METADATA"  # Ответ на запрос метаданных
    FRAME: ClassVar[str] = "FRAME"  # Ответ на запрос кадра

    def __init__(self, status: str = STATUS_OK, type_: str = GENERAL, **kwargs) -> None:  # type: ignore[no-untyped-def]
        kwargs['status'] = status
        super().__init__(type_=type_, **kwargs)

    @classmethod
    def ok_response(cls: Type[T], type_: str = GENERAL, **kwargs) -> T:  # type: ignore[no-untyped-def]
        """Создание успешного ответа"""
        return cls(status=cls.STATUS_OK, type_=type_, **kwargs)

    @classmethod
    def error_response(cls: Type[T], type_: str = GENERAL, **kwargs) -> T:  # type: ignore[no-untyped-def]
        """Создание ответа с ошибкой"""
        return cls(status=cls.STATUS_ERROR, type_=type_, **kwargs)

    def is_ok(self) -> bool:
        return self._fields.get('status') == self.STATUS_OK
