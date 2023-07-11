# defines a typed class variable, even it not defined in the class declaration
# experimental
from sinner.validators.BaseValidator import BaseValidator


class InitValidator(BaseValidator):

    def validate(self, validating_object: object, attribute: str) -> str | None:
        if getattr(validating_object, attribute) is None:
            setattr(validating_object.__class__, attribute, self.arguments['value'])
        return None
