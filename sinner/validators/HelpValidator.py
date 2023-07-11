from sinner.validators.BaseValidator import BaseValidator


# fake validator to support non-validators rules parameters
class HelpValidator(BaseValidator):

    def validate(self, validated_object: object, attribute: str) -> str | None:
        return None
