from typing import Dict, Any

from sinner.gui.server.api.messages.BaseMessage import BaseMessage


class BinaryDataMessage(BaseMessage):
    """
    Message class for binary data exchange
    Contains a binary_type field to identify the type of binary data
    """

    # Constants for binary types
    BINARY_FRAME = "BINARY_FRAME"
    BINARY_IMAGE = "BINARY_IMAGE"
    BINARY_FILE = "BINARY_FILE"

    def __init__(self, binary_type: str) -> None:
        super().__init__()
        if binary_type:
            self.binary_type = binary_type

    @property
    def binary_type(self) -> str:
        if hasattr(self, '_binary_type'):
            return self._binary_type
        else:
            raise ValueError("Field 'binary_type' is required")

    @binary_type.setter
    def binary_type(self, value: str) -> None:
        self._binary_type = value

    def validate(self) -> None:
        if not self.binary_type:
            raise ValueError("Field 'binary_type' is required")

    def to_dict(self) -> Dict[str, Any]:
        result = {'binary_type': self.binary_type} if self.binary_type else {}
        result.update(self._extra_fields)
        return result
