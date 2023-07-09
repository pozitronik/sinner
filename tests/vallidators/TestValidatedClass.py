from sinner.processors.BaseValidatedClass import BaseValidatedClass, Rules

DEFAULT_VALUE = 42


class TestDefaultValidation(BaseValidatedClass):
    default_parameter: int = None
    parameter_name: int = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'default_parameter', 'default': DEFAULT_VALUE},  # class.default_value = DEFAULT_VALUE
            {'parameter': 'parameter-name', 'default': DEFAULT_VALUE},  # class.parameter_name = DEFAULT_VALUE
        ]


class TestRequiredValidation(BaseValidatedClass):
    required_parameter: str = None
    default_required_parameter: int = None
    required_default_parameter: int = None

    def rules(self) -> Rules:
        return [
            {'parameter': 'required_parameter', 'required': True},  # Ok, if '--required_parameter' passed, else ValueRequired exception
            {'parameter': 'default_required_parameter', 'default': DEFAULT_VALUE, 'required': True},  # class.default_required_parameter = DEFAULT_VALUE, no error
            {'parameter': 'required_default_parameter', 'required': True, 'default': DEFAULT_VALUE},  # required validation made before default, so ValueRequired exception here (?)
        ]


class TestValidatedClass(BaseValidatedClass):
    required_parameter: str
    default_required_parameter: int
    required_default_parameter: int

    def rules(self) -> Rules:
        return [
            {'parameter': 'default_parameter', 'default': DEFAULT_VALUE},  # class.default_value = DEFAULT_VALUE
            {'parameter': 'parameter-name', 'default': DEFAULT_VALUE},  # class.parameter_name = DEFAULT_VALUE
            {'parameter': 'parameter_not_exists'},  # Validation error "TestValidatedClass has no attribute 'parameter_not_exists'"
            {'parameter': 'required_parameter', 'required': True},  # Ok, if '--required_parameter' passed, else ValueRequired exception
            {'parameter': 'default_required_parameter', 'default': DEFAULT_VALUE, 'required': True},  # class.default_required_parameter = DEFAULT_VALUE, no error
            {'parameter': 'required_default_parameter', 'required': True, 'default': DEFAULT_VALUE},  # required validation made before default, so ValueRequired exception here (?)
        ]
