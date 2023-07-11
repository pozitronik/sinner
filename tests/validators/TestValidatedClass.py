from abc import ABC
from typing import Any, List

from sinner.validators.AttributeLoader import AttributeLoader, Rules

DEFAULT_VALUE = 42


class TestDefaultValidation(AttributeLoader):
    default_parameter: int = None
    parameter_name: int = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'default_parameter', 'default': DEFAULT_VALUE},  # class.default_value = DEFAULT_VALUE
            {'parameter': 'parameter-name', 'default': DEFAULT_VALUE},  # class.parameter_name = DEFAULT_VALUE
        ]


class TestRequiredValidation(AttributeLoader):
    required_parameter: str = None
    default_required_parameter: int = None
    required_default_parameter: int = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'required_parameter', 'required': True},  # Ok, if '--required_parameter' passed, else ValueRequired exception
            {'parameter': 'default_required_parameter', 'default': DEFAULT_VALUE, 'required': True},  # class.default_required_parameter = DEFAULT_VALUE, no error
            {'parameter': 'required_default_parameter', 'required': True, 'default': DEFAULT_VALUE},  # required validation made before default, so ValueRequired exception here (?)
        ]


class TestUntypedAttribute(AttributeLoader):
    untyped_attribute: Any = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'untyped_attribute', 'required': True},
        ]


class TestEqualValueAttribute(AttributeLoader):
    int_attribute: int = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'int_attribute', 'value': 10},  # valid if value equal to 10
        ]


class TestInValueAttribute(AttributeLoader):
    in_list_attribute: int = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'in_list_attribute', 'value': [1, 7, 14, 42]},  # valid if value in [1, 7, 14, 42]
        ]


class TestLambdaValueAttribute(AttributeLoader):
    lambda_attribute: int = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'lambda_attribute', 'value': lambda attribute: self.valid(attribute)},  # valid if self.valid() is True
        ]

    def valid(self, attribute: str) -> bool:
        return 41 < getattr(self, attribute) < 43


class TestListAttribute(AttributeLoader, ABC):
    list_attribute: list[str] = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'list_attribute', 'default': ['Dolor', 'sit', 'amet']},
        ]


class TestInitAttribute(AttributeLoader):

    def rules(self) -> Rules:
        return [
            {'parameter': 'non_existent_parameter_type_list', 'type': List[str], 'default': ['Lorem', 'ipsum']},  # defines a class variable with type and assign a value to it
            {'parameter': 'non_existent_parameter_type_auto', 'default': ['Dolor', 'sit', 'amet']},  # defines a class variable with type and assign a value to it
            {'parameter': 'non_existent_parameter_type_int', 'type': int, 'default': 1, 'required': True},  # defines a class variable with type and assign a value to it
            {'parameter': 'non_existent_parameter_type_required', 'required': True},  # defines a class variable with type and assign a value to it
        ]


class TestInitAttributeTyped(AttributeLoader):
    non_existent_parameter_type_list: List[str]
    non_existent_parameter_type_auto: List[str]
    non_existent_parameter_type_int: int
    non_existent_parameter_type_required: Any

    def rules(self) -> Rules:
        return [
            {'parameter': 'non_existent_parameter_type_list', 'type': List[str], 'default': ['Lorem', 'ipsum']},  # defines a class variable with type and assign a value to it
            {'parameter': 'non_existent_parameter_type_auto', 'default': ['Dolor', 'sit', 'amet']},  # defines a class variable with type and assign a value to it
            {'parameter': 'non_existent_parameter_type_int', 'type': int, 'default': 1, 'required': True},  # defines a class variable with type and assign a value to it
            {'parameter': 'non_existent_parameter_type_required', 'required': True},  # defines a class variable with type and assign a value to it
        ]
