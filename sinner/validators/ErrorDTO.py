class ErrorDTO:
    attribute: str
    value: str | None = None
    message: str | None = None
    module: str | None = None
    validator: str | None = None
    help_message: str | None = None

    def __init__(self, attribute: str, value: str | None = None, message: str | None = None, module: str | None = None, validator: str | None = None, help_message: str | None = None):
        self.attribute = attribute
        self.value = value
        self.message = message
        self.module = module
        self.validator = validator
        self.help_message = help_message
