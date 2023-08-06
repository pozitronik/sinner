import inspect
from typing import Dict, Any, Iterable

from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.ErrorDTO import ErrorDTO
from sinner.validators.ValidatorException import ValidatorException


class ValueValidator(BaseValidator):
    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)  # useless call, but whatever
        self.arguments: Dict[str, Any] = {
            # assuming parameter necessary will be checked with RequiredValidator, this parameter can be always skipped
            'required': False
        }
        self.arguments.update(kwargs)

    def validate(self, validated_object: object, attribute: str) -> ErrorDTO | None:
        attribute_value = self.get_validated_attribute_value(validated_object, attribute)
        validation_value = self.arguments['value']
        if attribute_value is None and self.arguments['required'] is False:
            return None
        if isinstance(validation_value, bool):
            return None if validation_value else ErrorDTO(attribute=attribute, value=attribute_value, message="is not valid", validator=self.__class__.__name__)
        if callable(validation_value):
            try:
                callable_parameters_count = len(inspect.signature(validation_value).parameters)
                if 0 == callable_parameters_count:
                    value = validation_value()
                elif 1 == callable_parameters_count:
                    value = validation_value(attribute)
                elif 2 == callable_parameters_count:
                    value = validation_value(attribute, getattr(validated_object, attribute, None))
                else:
                    raise ValidatorException(f'More than 2 attribute is not allowed for validating lambdas ({callable_parameters_count} are present) for {attribute} attribute', validated_object, self)
                return None if value else ErrorDTO(attribute=attribute, value=attribute_value, message="is not valid", validator=self.__class__.__name__)
            except Exception:
                raise ValidatorException(f'Exception when retrieve callable value for {attribute} attribute', validated_object, self)

        if isinstance(validation_value, Iterable):
            if isinstance(attribute_value, Iterable) and not isinstance(attribute_value, str):
                return None if all(item in validation_value for item in attribute_value) else ErrorDTO(attribute=attribute, value=str(attribute_value), message=f"is not in {validation_value}", validator=self.__class__.__name__)
            else:
                return None if attribute_value in validation_value else ErrorDTO(attribute=attribute, value=str(attribute_value), message=f"is not in {validation_value}", validator=self.__class__.__name__)
        return None if attribute_value == validation_value else ErrorDTO(attribute=attribute, value=str(attribute_value), message=f"is not equal to {validation_value}", validator=self.__class__.__name__)
