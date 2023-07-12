import inspect

from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.ValidatorException import ValidatorException


class DefaultValidator(BaseValidator):

    def validate(self, validated_object: object, attribute: str) -> str | None:
        if self.get_validated_attribute_value(validated_object, attribute) is None:
            validation_value = self.arguments['value']
            if callable(validation_value):
                try:
                    callable_parameters_count = len(inspect.signature(validation_value).parameters)
                    if 0 == callable_parameters_count:
                        value = validation_value()
                    elif 1 == callable_parameters_count:
                        value = validation_value(attribute)
                    else:
                        raise ValidatorException(f'More than 1 attribute is not allowed for validating lambdas ({callable_parameters_count} are present) for {attribute} attribute', validated_object, self)
                except Exception:
                    raise ValidatorException(f'Exception when retrieve callable value for {attribute} attribute', validated_object, self)
            else:
                value = validation_value
            setattr(validated_object, attribute, value)
        return None
