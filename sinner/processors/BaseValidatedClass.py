from abc import abstractmethod, ABC
from argparse import Namespace
from typing import List, Any, Dict

Rule = Dict[str, str]
Rules = List[Rule]


class Validator(ABC):
    @abstractmethod
    def validate(self, value: Any) -> str | None:  # text error or None, if valid
        pass


class BaseValidatedClass:
    errors: List[dict[str, str]]  # list of parameters validation errors, attribute: error

    @abstractmethod
    def rules(self) -> Rules:
        return []

    def load(self, attributes: Namespace, validate: bool = True) -> bool:
        for attribute in attributes:
            if hasattr(self, attribute):
                self['attribute'] = attributes['attribute']
            else:
                return False
        if validate:
            return self.validate()
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
            print(f"Module {error['module']} has {error['attribute']}: {error['error']}")

    def validate_attribute(self, attribute: str) -> List[str]:  # returns a list of errors on attribute
        errors: List[str] = []
        for rule in self.get_attribute_rules(attribute):
            validator = self.get_rule_validator(rule)
            error = validator.validate(self['attribute'])
            if error is not None:
                errors.append(error)
        return errors

    # returns the list of attributes names, which listed in the `rules` configuration
    def validating_attributes(self) -> List[str]:
        pass

    # return all rules configurations for attribute
    def get_attribute_rules(self, attribute: str) -> Rules:
        pass

    # returns validator object for current rule
    def get_rule_validator(self, rule: Rule) -> 'Validator':
        pass
