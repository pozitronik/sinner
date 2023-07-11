from argparse import Namespace
from typing import List, Dict, Any, Type

from sinner.utilities import declared_attr_type
from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.DefaultValidator import DefaultValidator
from sinner.validators.HelpValidator import HelpValidator
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
    'help': HelpValidator
}


class AttributeLoader:
    errors: List[dict[str, str]] = []  # list of parameters validation errors, attribute: error, help: help message
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
            if declared_attr_type(self, attribute) is not None:
                self.setattr(attribute, value)  # the values should be loaded before validation
        if validate:
            if not self.validate():  # return values back
                self.restore_attributes()
                return False
        return True

    def validate(self) -> bool:
        validating_attributes = self.validating_attributes()
        self.init_declared_attributes(validating_attributes)
        for attribute in validating_attributes:
            for error in self.validate_attribute(attribute):
                self.add_error(attribute=attribute, error=error, module=self.__class__.__name__)
        return [] == self.errors

    def add_error(self, attribute: str, error: str = 'invalid value', module: str = '😈sinner') -> None:
        self.errors.append({'attribute': attribute, 'error': error, 'module': module, 'help': self.get_attribute_help(attribute)})

    def validate_attribute(self, attribute: str) -> List[str]:  # returns a list of errors on attribute
        if not declared_attr_type(self, attribute):  # doesn't allow to use dynamic attributes
            raise LoaderException(f'Property {attribute} is not declared in a class', self, attribute)
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
        attribute_type = declared_attr_type(self, attribute)
        if attribute_type is None:
            raise LoaderException(f'Property {attribute} is not declared in a class', self, attribute)
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

    def init_declared_attributes(self, attribute_list: List[str]) -> None:
        for attribute in attribute_list:
            if hasattr(self, attribute) is False and declared_attr_type(self, attribute) is not None:  # attribute is type declared
                setattr(self, attribute, None)

    def get_attribute_help(self, attribute: str) -> str | None:
        attribute_help = self.get_attribute_rules(attribute)
        return attribute_help['help'] if 'help' in attribute_help else None