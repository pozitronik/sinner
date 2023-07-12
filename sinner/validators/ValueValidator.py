import inspect
from typing import Dict, Any, Iterable

from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.ValidatorException import ValidatorException


class ValueValidator(BaseValidator):
    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)  # useless call, but whatever
        self.arguments: Dict[str, Any] = {
            # assuming parameter necessary will be checked with RequiredValidator, this parameter can be always skipped
            'required': False
        }
        self.arguments.update(kwargs)

    def validate(self, validated_object: object, attribute: str) -> str | None:
        attribute_value = self.get_validated_attribute_value(validated_object, attribute)
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
                    raise ValidatorException(f'More than 1 attribute is not allowed for validating lambdas ({callable_parameters_count} are present) for {attribute} attribute', validated_object, self)
                return None if value else f"={attribute_value} is not valid"
            except Exception:
                raise ValidatorException(f'Exception when retrieve callable value for {attribute} attribute', validated_object, self)

        if isinstance(validation_value, Iterable):
            if isinstance(attribute_value, Iterable):
                return None if all(item in validation_value for item in attribute_value) else f"={attribute_value} is not in {validation_value}"
            else:
                return None if attribute_value in validation_value else f"={attribute_value} is not in {validation_value}"
        return None if attribute_value == validation_value else f"{attribute_value} is not equal to {validation_value}"
