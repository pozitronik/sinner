from sinner.validators.BaseValidator import BaseValidator


class RequiredValidator(BaseValidator):
    DEFAULT_MESSAGE = 'Attribute is required'

    def validate(self, validating_object: object, attribute: str) -> str | None:
        if self.arguments['value'] is True and getattr(validating_object, attribute) is None:
            return self.DEFAULT_MESSAGE
        return None
