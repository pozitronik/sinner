from abc import abstractmethod, ABC
from argparse import Namespace
from typing import List, Dict, Any
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


VALIDATORS = {
    'default': DefaultValidator,
    'required': RequiredValidator,
    # 'choices': ChoicesValidator,
    # 'in': ChoicesValidator,
    # 'type': TypeValidator,
    # 'action': ActionValidator,
    # 'valid': CallableValidator,
    # 'function': CallableValidator,
    # 'lambda': CallableValidator
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
        for key in vars(self.old_attributes):
            delattr(self.old_attributes, key)
        for attribute, value in self.get_class_attributes():
            setattr(self.old_attributes, attribute, getattr(self, attribute))

    def restore_attributes(self):
        for attribute, value in vars(self.old_attributes).items():
            setattr(self, attribute, value)

    def load(self, attributes: Namespace, validate: bool = True) -> bool:
        self.save_attributes()
        for attribute, value in vars(attributes).items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)  # the values should be loaded before validation
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
                ruleset.update(rule)
        return ruleset

    # returns validators objects for current rule
    @staticmethod
    def get_rule_validators(rule: Rule) -> List['Validator']:
        validators: List['Validators'] = []
        rule.pop('parameter')
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
