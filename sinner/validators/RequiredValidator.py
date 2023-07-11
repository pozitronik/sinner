from sinner.validators.BaseValidator import BaseValidator


class RequiredValidator(BaseValidator):
    DEFAULT_MESSAGE = 'Attribute is required'

    def validate(self, validated_object: object, attribute: str) -> str | None:
        if self.arguments['value'] is True and self.get_validated_attribute_value(validated_object, attribute) is None:
            return self.DEFAULT_MESSAGE
        return None
