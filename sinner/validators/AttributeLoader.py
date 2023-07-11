from argparse import Namespace
from typing import List, Dict, Any, get_type_hints, Type
from colorama import Fore

from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.DefaultValidator import DefaultValidator
from sinner.validators.InitValidator import InitValidator
from sinner.validators.LoaderException import LoaderException
from sinner.validators.RequiredValidator import RequiredValidator
from sinner.validators.ValueValidator import ValueValidator

Rule = Dict[str, Any]
Rules = List[Rule]

'''
Rule = {'parameter': 'parameter_name', 'validator_name': validator_parameters}
validator_parameters can be a scalar value or a dict of a key-value pairs 
'''

# defines the correspondence between validator string name and its class
# also define the order validators applied
VALIDATORS: dict[str, Type[BaseValidator]] = {
    'init': InitValidator,
    'type': InitValidator,
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


class AttributeLoader:
    allow_dynamic_attributes: bool = True  # if True, validated attribute will be created in runtime, else LoaderException will be thrown. Use a InitValidator to dynamically create properties with desired types
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
        if self.allow_dynamic_attributes is False and not hasattr(self, attribute):  # doesn't allow to use dynamic attributes
            raise LoaderException(self, attribute)

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
    def get_rule_validators(rule: Rule) -> List[BaseValidator]:
        validators: List[BaseValidator] = []
        for validator_name, validator_parameters in rule.items():
            if validator_name in VALIDATORS:
                validator_class: Type[BaseValidator] = VALIDATORS[validator_name]
                if not isinstance(validator_parameters, dict):  # convert scalar values to **kwargs dict
                    validator_parameters = {'value': validator_parameters}
                validators.append(validator_class(**validator_parameters))  # initialize validator class with parameters
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
