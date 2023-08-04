import inspect

from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.ValidatorException import ValidatorException


class RequiredValidator(BaseValidator):
    DEFAULT_MESSAGE = 'is required'

    def validate(self, validated_object: object, attribute: str) -> str | None:
        validation_value = self.arguments['value']
        if callable(validation_value):
            try:
                callable_parameters_count = len(inspect.signature(validation_value).parameters)
                if 0 == callable_parameters_count:
                    validation_value = validation_value()
                elif 1 == callable_parameters_count:
                    validation_value = validation_value(attribute)
                elif 2 == callable_parameters_count:
                    validation_value = validation_value(attribute, getattr(validated_object, attribute, None))
                else:
                    raise ValidatorException(f'More than 2 attribute is not allowed for validating lambdas ({callable_parameters_count} are present) for {attribute} attribute', validated_object, self)
            except Exception:
                raise ValidatorException(f'Exception when retrieve callable value for {attribute} attribute', validated_object, self)
        return self.DEFAULT_MESSAGE if bool(validation_value) is True and self.get_validated_attribute_value(validated_object, attribute) is None else None
