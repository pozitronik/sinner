from sinner.validators.BaseValidator import BaseValidator
from sinner.validators.ErrorDTO import ErrorDTO


# fake validator to support non-validators rules parameters
class HelpValidator(BaseValidator):

    def validate(self, validated_object: object, attribute: str) -> ErrorDTO | None:
        return None
