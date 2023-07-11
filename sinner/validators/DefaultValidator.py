from sinner.validators.BaseValidator import BaseValidator


class DefaultValidator(BaseValidator):

    def validate(self, validating_object: object, attribute: str) -> str | None:
        if getattr(validating_object, attribute) is None:
            setattr(validating_object, attribute, self.arguments['value'])
        return None
