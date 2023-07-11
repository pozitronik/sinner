from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseValidator(ABC):
    arguments: Dict[str, Any]  # shouldn't be initialized with list to prevent sharing value between classes

    def __init__(self, **kwargs: Dict[str, Any]):
        self.arguments: Dict[str, Any] = {}
        self.arguments.update(kwargs)

    @abstractmethod
    def validate(self, validating_object: object, attribute: str) -> str | None:  # text error or None, if valid
        pass