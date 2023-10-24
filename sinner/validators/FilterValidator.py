import inspect

from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.ErrorDTO import ErrorDTO
from sinner.validators.ValidatorException import ValidatorException


# applies a filter on the input value and assigns it back to the attribute being validated.
class FilterValidator(BaseValidator):

    def validate(self, validated_object: object, attribute: str) -> ErrorDTO | None:
        filter_method = self.arguments['value']
        attribute_value = self.get_validated_attribute_value(validated_object, attribute)
        if callable(filter_method):
            try:
                callable_parameters_count = len(inspect.signature(filter_method).parameters)
                if 0 == callable_parameters_count:
                    value = filter_method()
                elif 1 == callable_parameters_count:
                    value = filter_method(attribute_value)
                else:
                    raise ValidatorException(f'More than 1 attribute is not allowed in filter lambdas ({callable_parameters_count} are present) for {attribute} attribute', validated_object, self)
                setattr(validated_object, attribute, value)
                return None
            except Exception as exception:
                raise ValidatorException(f'{type(exception).__name__} with message `{str(exception)}` when retrieve callable value for {attribute} attribute', validated_object, self)
        return ErrorDTO(attribute=attribute, value=attribute_value, message="Callable expected", validator=self.__class__.__name__)
