from abc import abstractmethod, ABC
from argparse import Namespace
from typing import List, Dict, Any, get_type_hints, Iterable
from colorama import Fore

Rule = Dict[str, str]
Rules = List[Rule]

'''
Rule = {'parameter': 'parameter_name', 'validator_name': validator_parameters}
validator_parameters can be a scalar value or a dict of a key-value pairs 
'''


class Validator(ABC):
    arguments: Dict

    def __init__(self, **kwargs):
        self.arguments = kwargs

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


class ValueValidator(Validator):

    def validate(self, validating_object: object, attribute: str) -> str | None:
        attribute_value = getattr(validating_object, attribute)
        validation_value = self.arguments['value']
        if callable(validation_value):
            return None if validation_value(attribute) else f"Value {attribute_value} is not in validation"
        if isinstance(self.arguments['value'], Iterable):
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
VALIDATORS = {
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

    @abstractmethod
    def rules(self) -> Rules:
        return []

    def get_class_attributes(self) -> List[tuple[str, Any]]:
        return [(attr, value) for attr, value in vars(self.__class__).items() if not attr.startswith('__') and not callable(value)]

    # saves all attribute and its values to a namespace object
    def save_attributes(self):
        vars(self.old_attributes).clear()
        for attribute, value in self.get_class_attributes():
            setattr(self.old_attributes, attribute, getattr(self, attribute))

    def restore_attributes(self):
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
                self.add_error(attribute=attribute, error=error)
        return [] == self.errors

    def add_error(self, attribute: str, error: str = 'invalid value', module: str = '😈sinner') -> None:
        self.errors.append({'attribute': attribute, 'error': error, 'module': module})

    def write_errors(self):
        for error in self.errors:
            print(f"Module {Fore.CYAN}{error['module']}{Fore.RESET} has error on {Fore.YELLOW}{error['attribute']}{Fore.RESET}: {Fore.RED}{error['error']}{Fore.RESET}")

    def validate_attribute(self, attribute: str) -> List[str]:  # returns a list of errors on attribute
        if not hasattr(self, attribute):  # doesn't allow to use dynamic attributes
            return [f'{__class__.__name__} has no attribute {attribute} defined']
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
    def get_rule_validators(rule: Rule) -> List['Validator']:
        validators: List['Validator'] = []
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
        attribute_type = get_type_hints(self)[attribute]
        try:
            if attribute_type.__name__ == 'list':
                if isinstance(value, list):
                    typed_value = value
                else:
                    typed_value = [value]
            else:
                typed_value = attribute_type(value)
        except Exception:  # if attribute has no type, or defined as Any, just ignore type casting
            typed_value = value
        setattr(self, attribute, typed_value)
