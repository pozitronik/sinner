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


class TestFilterValidation(AttributeLoader):
    filtered_parameter: Any = None
    filtered_parameter_2: int = None

    @staticmethod
    def filter_lambda(value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, float) or isinstance(value, int):
            if value < 0:
                value = 0
            if value > 100:
                value = 100
        return value

    def rules(self) -> Rules:
        return [
            {'parameter': 'filtered_parameter', 'filter': lambda: self.filter_lambda(self.filtered_parameter)},
            {'parameter': 'filtered_parameter_2', 'filter': lambda param: self.filter_lambda(param)},
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


class TestRequiredValidationLambda(AttributeLoader):
    required_lambda_parameter: int = None
    not_required_lambda_parameter: bool = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'required_lambda_parameter', 'required': lambda: self.valid_lambda()},  # required
            {'parameter': 'not_required_lambda_parameter', 'required': lambda: self.invalid_lambda()},  # not required
        ]

    @staticmethod
    def valid_lambda() -> bool:
        return True

    @staticmethod
    def invalid_lambda() -> int:
        return 0


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
    non_existent_parameter_type_auto: Any
    non_existent_parameter_type_int: int
    non_existent_parameter_type_required: Any

    def rules(self) -> Rules:
        return [
            {'parameter': 'non_existent_parameter_type_list', 'type': List[str], 'default': ['Lorem', 'ipsum']},  # defines a class variable with type and assign a value to it
            {'parameter': 'non_existent_parameter_type_auto', 'default': ['Dolor', 'sit', 'amet']},  # defines a class variable with type and assign a value to it
            {'parameter': 'non_existent_parameter_type_int', 'type': int, 'default': 1, 'required': True},  # defines a class variable with type and assign a value to it
            {'parameter': 'non_existent_parameter_type_required', 'required': True},  # defines a class variable with type and assign a value to it
        ]


class TestParameterAliases(AttributeLoader):
    param_one: int
    param_two: str
    param_three: str

    def rules(self) -> Rules:
        return [
            {'parameter': ['param-one', 'param1', 'p1'], 'attribute': 'param_one'},
            {'parameter': ['param-two', 'param2', 'p2'], 'attribute': 'param_two'},
            {'parameter': ['param-three', 'param3', 'p3']},
        ]


# rule only with attributes
class TestParameterAttributes(AttributeLoader):
    param_one: int
    param_two: str

    def rules(self) -> Rules:
        return [
            {'attribute': 'param_one'},
            {'attribute': 'param_two'},
        ]
