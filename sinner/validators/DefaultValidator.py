from sinner.validators.BaseValidator import BaseValidator


class DefaultValidator(BaseValidator):

    def validate(self, validated_object: object, attribute: str) -> str | None:
        if self.get_validated_attribute_value(validated_object, attribute) is None:
            setattr(validated_object, attribute, self.arguments['value'])
        return None
