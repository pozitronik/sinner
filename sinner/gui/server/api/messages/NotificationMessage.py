from typing import ClassVar,TypeVar

from sinner.gui.server.api.messages.BaseMessage import BaseMessage

T = TypeVar('T', bound='NotificationMessage')


class NotificationMessage(BaseMessage):
    """
    Класс для отправки нотификаций клиенту
    """

    NTF_FRAME: ClassVar[str] = "NTF_FRAME"  # оповещение о готовности фрейма
