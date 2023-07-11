from abc import ABC, abstractmethod
from typing import Dict, Any

from sinner.utilities import declared_attr_type


class BaseValidator(ABC):
    arguments: Dict[str, Any]  # shouldn't be initialized with list to prevent sharing value between classes

    def __init__(self, **kwargs: Dict[str, Any]):
        self.arguments: Dict[str, Any] = {}
        self.arguments.update(kwargs)

    @abstractmethod
    def validate(self, validated_object: object, attribute: str) -> str | None:  # text error or None, if valid
        pass

    @staticmethod
    def get_validated_attribute_value(validated_object: object, attribute: str) -> Any:
        """
        returns a value of a class attribute. Attribute should be either initialized with value either have a type declaration
        :param validated_object:
        :param attribute:
        :return:
        """
        if hasattr(validated_object, attribute) is False and declared_attr_type(validated_object, attribute) is not None:  # attribute typed declaration without any value
            attribute_value = None
        else:
            attribute_value = getattr(validated_object, attribute)
        return attribute_value
