import inspect

from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.ErrorDTO import ErrorDTO
from sinner.validators.ValidatorException import ValidatorException


class RequiredValidator(BaseValidator):

    def validate(self, validated_object: object, attribute: str) -> ErrorDTO | None:
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
        attribute_value = self.get_validated_attribute_value(validated_object, attribute)
        return ErrorDTO(attribute=attribute, value=str(attribute_value), message="is required", validator=self.__class__.__name__) if bool(validation_value) is True and attribute_value is None else None
