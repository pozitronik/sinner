from sinner.processors.BaseValidatedClass import BaseValidatedClass


def get_test_object() -> 'TestValidatedClass':
    return BaseValidatedClass()


def test_default_validator() -> None:
    pass


def test_required_validator() -> None:
    pass
