# defines a typed class variable, even it not defined in the class declaration
# also casts the variable type to the specified type
from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.ValidatorException import ValidatorException


class InitValidator(BaseValidator):

    def validate(self, validating_object: object, attribute: str) -> str | None:
        attribute_type_name = None
        new_value = None
        try:
            attribute_type = self.arguments['value']
            attribute_type_name = attribute_type.__origin__.__name__ if hasattr(attribute_type, '__origin__') else attribute_type.__name__
            current_value = getattr(validating_object, attribute, None)
            if attribute_type_name == 'list':
                if isinstance(current_value, list):
                    new_value = current_value
                else:
                    new_value = [current_value]
            else:
                new_value = attribute_type(current_value)
            setattr(validating_object, attribute, new_value)
            return None
        except Exception:
            raise ValidatorException(f"Exception when trying to initialize property {property} with value ({attribute_type_name}){new_value}", validating_object, self)
