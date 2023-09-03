from argparse import Namespace
from typing import List, Dict, Any, Type

from sinner.utilities import declared_attr_type
from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.DefaultValidator import DefaultValidator
from sinner.validators.ErrorDTO import ErrorDTO
from sinner.validators.HelpValidator import HelpValidator
from sinner.validators.LoaderException import LoaderException, LoadingException
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
    errors: List[ErrorDTO] = []  # list of parameters validation errors
    old_attributes: Namespace = Namespace()  # previous values (before loading)

    def rules(self) -> Rules:
        return []

    def __init__(self, parameters: Namespace = Namespace()):
        if not self.load(parameters):
            raise LoadingException(self.errors)

    # returns all initialized class variables with values, except properties
    def get_class_attributes(self) -> List[tuple[str, Any]]:
        return [(attr, value) for attr, value in vars(self.__class__).items() if not attr.startswith('__') and not callable(value) and not isinstance(value, property)]

    # saves all attribute and its values to a namespace object
    def save_attributes(self) -> None:
        vars(self.old_attributes).clear()
        for attribute, value in self.get_class_attributes():
            setattr(self.old_attributes, attribute, getattr(self, attribute))

    def restore_attributes(self) -> None:
        for attribute, value in vars(self.old_attributes).items():
            setattr(self, attribute, value)

    def load(self, parameters: Namespace, validate: bool = True) -> bool:
        self.errors.clear()
        self.save_attributes()
        for key, value in vars(parameters).items():
            attribute = self.find_rule_attribute(key)
            if attribute is not None and declared_attr_type(self, attribute) is not None:
                self.setattr(attribute, value)  # the values should be loaded before validation
        if validate:
            if not self.validate():  # return values back
                self.restore_attributes()
                return False
        return True

    # by key name finds class parameter to load key value
    def find_rule_attribute(self, key: str) -> str | None:
        for rule in self.rules():
            if 'parameter' in rule:
                parameter = rule['parameter']
                if isinstance(parameter, str):
                    parameter = [parameter]
                if isinstance(parameter, (list, set)):
                    if key in parameter or key.replace('-', '_') in parameter or key.replace('_', '-') in parameter:
                        return rule['attribute'] if 'attribute' in rule else list(parameter)[0].replace('-', '_')
            if 'attribute' in rule:
                if rule['attribute'] == key.replace('-', '_'):
                    return rule['attribute']
        return None

    # by attribute name return all its parameters
    def get_attribute_parameters(self, attribute: str) -> List[str]:
        for rule in self.rules():
            if 'attribute' in rule:
                if rule['attribute'] == attribute.replace('-', '_'):
                    if isinstance(rule['parameter'], str):
                        return [rule['parameter']]
                    else:
                        return list(rule['parameter'])
            if 'parameter' in rule:
                parameter = rule['parameter']
                if isinstance(parameter, str):
                    parameter = [parameter]
                if isinstance(parameter, (list, set)):
                    if attribute in parameter or attribute.replace('-', '_') in parameter or attribute.replace('_', '-') in parameter:
                        return list(parameter)
        return []

    def validate(self, stop_on_error: bool = True) -> bool:
        validating_attributes = self.validating_attributes()
        self.init_declared_attributes(validating_attributes)
        for attribute in validating_attributes:
            for error in self.validate_attribute(attribute):
                self.add_error(error=error, module=self.__class__.__name__)
                if stop_on_error:
                    return False
        return [] == self.errors

    def add_error(self, error: ErrorDTO, module: str = '😈sinner') -> None:
        error.module = module
        error.help_message = self.get_attribute_help(error.attribute)
        self.errors.append(error)

    def validate_attribute(self, attribute: str) -> List[ErrorDTO]:  # returns a list of errors on attribute
        if not declared_attr_type(self, attribute):  # doesn't allow to use dynamic attributes
            raise LoaderException(f'Property {attribute} is not declared in a class', self, attribute)
        rule = self.get_attribute_rules(attribute)
        errors: List[ErrorDTO] = []
        for validator in self.get_rule_validators(rule):
            error = validator.validate(self, attribute)
            if error is not None:
                errors.append(error)
        return errors

    # returns the list of attributes names, which listed in the `rules` configuration
    def validating_attributes(self) -> List[str]:
        values: List[str] = []
        for rule in self.rules():
            if 'attribute' in rule:
                values.append(rule['attribute'])
            elif 'parameter' in rule:
                if isinstance(rule['parameter'], str):
                    values.append(rule['parameter'].replace('-', '_'))
                elif isinstance(rule['parameter'], (list, set)):
                    values.append(list(rule['parameter'])[0].replace('-', '_'))
            # else rule ignored
        return values

    # return all rules configurations for attribute combined to one rule
    def get_attribute_rules(self, attribute: str) -> Rule:
        ruleset = {}
        for rule in self.rules():
            if self.is_rule_attribute(rule, attribute):
                rule = self.streamline_rule_order(rule)
                ruleset.update(rule)
        return ruleset

    @staticmethod
    def is_rule_attribute(rule: Rule, attribute: str) -> bool:
        if 'attribute' in rule:
            return rule['attribute'] == attribute
        elif 'parameter' in rule:
            if isinstance(rule['parameter'], str):
                return rule['parameter'].replace('-', '_') == attribute
            elif isinstance(rule['parameter'], (list, set)):
                return list(rule['parameter'])[0].replace('-', '_') == attribute
        return False

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
            typed_value: Any
            if attribute_type_name == 'list':
                if isinstance(value, list):
                    typed_value = value
                else:
                    typed_value = [value]
            elif attribute_type_name == 'bool':
                typed_value = not value.lower() in ['false', 'f', '0', 'n', 'no']
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

    def get_module_help(self) -> str | None:
        for rule in self.rules():
            if 'module_help' in rule:
                return rule['module_help']
        return None

    # get all initialized attributes, enlisted in cls.rules() and update parameters
    def update_parameters(self, parameters: Namespace) -> None:
        attributes = self.validating_attributes()
        for attribute in attributes:
            setattr(parameters, attribute, getattr(self, attribute, None))

    @property
    def validated_attributes(self) -> List[tuple[str, Any]]:
        result: List[tuple[str, Any]] = []
        for attribute in self.validating_attributes():
            result.append((attribute, getattr(self, attribute)))
        return result
