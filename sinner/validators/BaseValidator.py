from abc import ABC, abstractmethod
from typing import Dict, Any

from sinner.utilities import declared_attr_type
from sinner.validators.ErrorDTO import ErrorDTO
from sinner.validators.ValidatorException import ValidatorException


class BaseValidator(ABC):
    arguments: Dict[str, Any]  # shouldn't be initialized with list to prevent sharing value between classes

    def __init__(self, **kwargs: Dict[str, Any]):
        self.arguments: Dict[str, Any] = {}
        self.arguments.update(kwargs)

    @abstractmethod
    def validate(self, validated_object: object, attribute: str) -> ErrorDTO | None:  # text error or None, if valid
        pass

    def get_validated_attribute_value(self, validated_object: object, attribute: str) -> Any:
        """
        returns a value of a class attribute. Attribute should be either initialized with value either have a type declaration
        :param validated_object:
        :param attribute:
        :return:
        """
        if declared_attr_type(validated_object, attribute) is not None:  # attribute typed declaration without any value
            return getattr(validated_object, attribute, None)
        raise ValidatorException(f'Property {attribute} is not declared in a class', validated_object, self)
