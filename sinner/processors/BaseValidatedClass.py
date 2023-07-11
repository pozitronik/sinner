import inspect
from abc import abstractmethod, ABC
from argparse import Namespace
from typing import List, Dict, Any, get_type_hints, Iterable
from colorama import Fore, Style, Back

Rule = Dict[str, Any]
Rules = List[Rule]

'''
Rule = {'parameter': 'parameter_name', 'validator_name': validator_parameters}
validator_parameters can be a scalar value or a dict of a key-value pairs 
'''


class Validator(ABC):
    arguments: Dict[str, Any]  # shouldn't be initialized with list to prevent sharing value between classes

    def __init__(self, **kwargs: Dict[str, Any]):
        self.arguments: Dict[str, Any] = {}
        self.arguments.update(kwargs)

    @abstractmethod
    def validate(self, validating_object: object, attribute: str) -> str | None:  # text error or None, if valid
        pass


class RequiredValidator(Validator):
    DEFAULT_MESSAGE = 'Attribute is required'

    def validate(self, validating_object: object, attribute: str) -> str | None:
        if self.arguments['value'] is True and getattr(validating_object, attribute) is None:
            return self.DEFAULT_MESSAGE
        return None


class DefaultValidator(Validator):

    def validate(self, validating_object: object, attribute: str) -> str | None:
        if getattr(validating_object, attribute) is None:
            setattr(validating_object, attribute, self.arguments['value'])
        return None


class ValidatorException(Exception):
    message: str
    validated_object: object
    validator_object: Validator

    def __init__(self, message: str, validated_object: object, validator_object: Validator):
        self.message = message
        self.validated_object = validated_object
        self.validator_object = validator_object

    def __str__(self) -> str:
        return f"{Fore.BLACK}{Back.RED}{self.validator_object.__class__.__name__}{Back.RESET}{Fore.RESET}: {self.message}@{Style.BRIGHT}{self.validated_object.__class__.__name__}{Style.RESET_ALL}"


class ValueValidator(Validator):
    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)  # useless call, but whatever
        self.arguments: Dict[str, Any] = {
            # assuming parameter necessary will be checked with RequiredValidator, this parameter can be always skipped
            'required': False
        }
        self.arguments.update(kwargs)

    def validate(self, validating_object: object, attribute: str) -> str | None:
        attribute_value = getattr(validating_object, attribute)
        validation_value = self.arguments['value']
        if attribute_value is None and self.arguments['required'] is False:
            return None
        if isinstance(validation_value, bool):
            return None if validation_value else f"Value {attribute_value} is not valid"
        if callable(validation_value):
            try:
                callable_parameters_count = len(inspect.signature(validation_value).parameters)
                if 0 == callable_parameters_count:
                    value = validation_value()
                elif 1 == callable_parameters_count:
                    value = validation_value(attribute)
                else:
                    raise ValidatorException(f'More than 1 attribute is not allowed for validating lambdas ({callable_parameters_count} are present) for {attribute} attribute', validating_object, self)
                return None if value else f"Value {attribute_value} is not valid"
            except Exception:
                raise ValidatorException(f'Exception when retrieve callable value for {attribute} attribute', validating_object, self)

        if isinstance(validation_value, Iterable):
            if isinstance(attribute_value, Iterable):
                return None if all(item in validation_value for item in attribute_value) else f"Value {attribute_value} is not in {validation_value}"
            else:
                return None if attribute_value in validation_value else f"Value {attribute_value} is not in {validation_value}"
        return None if attribute_value == validation_value else f"Value {attribute_value} is not equal to {validation_value}"


# defines a typed class variable, even it not defined in the class declaration
# experimental
class InitValidator(Validator):

    def validate(self, validating_object: object, attribute: str) -> str | None:
        if getattr(validating_object, attribute) is None:
            setattr(validating_object.__class__, attribute, self.arguments['value'])
        return None


# defines the correspondence between validator string name and its class
# also define the order validators applied
VALIDATORS: dict[str, type] = {
    # 'init': InitValidator,
    # 'type': InitValidator,
    'default': DefaultValidator,
    'required': RequiredValidator,
    'value': ValueValidator,
    'valid': ValueValidator,
    'choices': ValueValidator,
    'in': ValueValidator,
    'action': ValueValidator,
    'function': ValueValidator,
    'lambda': ValueValidator,
}


class BaseValidatedClass:
    errors: List[dict[str, str]] = []  # list of parameters validation errors, attribute: error
    old_attributes: Namespace = Namespace()  # previous values (before loading)

    def rules(self) -> Rules:
        return []

    def get_class_attributes(self) -> List[tuple[str, Any]]:
        return [(attr, value) for attr, value in vars(self.__class__).items() if not attr.startswith('__') and not callable(value)]

    # saves all attribute and its values to a namespace object
    def save_attributes(self) -> None:
        vars(self.old_attributes).clear()
        for attribute, value in self.get_class_attributes():
            setattr(self.old_attributes, attribute, getattr(self, attribute))

    def restore_attributes(self) -> None:
        for attribute, value in vars(self.old_attributes).items():
            setattr(self, attribute, value)

    def load(self, attributes: Namespace, validate: bool = True) -> bool:
        self.errors.clear()
        self.save_attributes()
        for attribute, value in vars(attributes).items():
            attribute = attribute.replace('-', '_')
            if hasattr(self, attribute):
                self.setattr(attribute, value)  # the values should be loaded before validation
        if validate:
            if not self.validate():  # return values back
                self.restore_attributes()
                return False
        return True

    def validate(self) -> bool:
        for attribute in self.validating_attributes():
            for error in self.validate_attribute(attribute):
                self.add_error(attribute=attribute, error=error, module=self.__class__.__name__)
        return [] == self.errors

    def add_error(self, attribute: str, error: str = 'invalid value', module: str = '😈sinner') -> None:
        self.errors.append({'attribute': attribute, 'error': error, 'module': module})

    def write_errors(self) -> None:
        for error in self.errors:
            print(f"Module {Fore.CYAN}{error['module']}{Fore.RESET} has validation error on {Fore.YELLOW}{error['attribute']}{Fore.RESET}: {Fore.RED}{error['error']}{Fore.RESET}")

    def validate_attribute(self, attribute: str) -> List[str]:  # returns a list of errors on attribute
        if not hasattr(self, attribute):  # doesn't allow to use dynamic attributes
            return [f'{self.__class__.__name__} has no attribute {attribute} defined']
        rule = self.get_attribute_rules(attribute)
        errors: List[str] = []
        for validator in self.get_rule_validators(rule):
            error = validator.validate(self, attribute)
            if error is not None:
                errors.append(error)
        return errors

    # returns the list of attributes names, which listed in the `rules` configuration
    def validating_attributes(self) -> List[str]:
        values = list(set([d['parameter'] for d in self.rules()]))
        values = [s.replace('-', '_') for s in values]  # parameters can contain '-', but attributes are not
        return values

    # return all rules configurations for attribute combined to one rule
    def get_attribute_rules(self, attribute: str) -> Rule:
        ruleset = {}
        for rule in self.rules():
            if rule['parameter'].replace('-', '_') == attribute:
                rule.pop('parameter')
                rule = self.streamline_rule_order(rule)
                ruleset.update(rule)
        return ruleset

    # returns validators objects for current rule
    @staticmethod
    def get_rule_validators(rule: Rule) -> List[Validator]:
        validators: List[Validator] = []
        for validator_name, validator_parameters in rule.items():
            if validator_name in VALIDATORS:
                validator_class = VALIDATORS[validator_name]
                if not isinstance(validator_parameters, dict):  # convert scalar values to **kwargs dict
                    validator_parameters = {'value': validator_parameters}
                validator_class = validator_class(**validator_parameters)  # initialize validator class with parameters
                validators.append(validator_class)
            else:
                print(f'Validator `{validator_name}` is not implemented')
        return validators

    @staticmethod
    def streamline_rule_order(rule: Rule) -> Rule:
        ordered_keys = list(VALIDATORS.keys())
        sorted_dict = {key: rule[key] for key in ordered_keys if key in rule}
        return sorted_dict

    def setattr(self, attribute: str, value: Any) -> None:
        attribute_type = get_type_hints(self.__class__)[attribute]
        try:
            attribute_type_name = attribute_type.__origin__.__name__ if hasattr(attribute_type, '__origin__') else attribute_type.__name__
            if attribute_type_name == 'list':
                if isinstance(value, list):
                    typed_value = value
                else:
                    typed_value = [value]
            else:
                typed_value = attribute_type(value)
        except Exception:  # if attribute has no type, or defined as Any, just ignore type casting
            typed_value = value
        setattr(self, attribute, typed_value)
