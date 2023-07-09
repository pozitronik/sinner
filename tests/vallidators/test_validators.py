import shlex
from argparse import ArgumentParser, Namespace

from sinner.Parameters import Parameters
from tests.vallidators.TestValidatedClass import DEFAULT_VALUE, TestDefaultValidation, TestRequiredValidation


def command_line_to_namespace(cmd_params: str) -> Namespace:
    args_list = shlex.split(cmd_params, posix=False)
    parser = ArgumentParser()
    args, unknown_args = parser.parse_known_args(args_list)
    for argument in unknown_args:
        key, value = Parameters.parse_argument(argument)
        setattr(args, key, value)
    return args


def test_default_validator() -> None:
    parameters: Namespace = command_line_to_namespace('')
    test_object = TestDefaultValidation()

    assert test_object.default_parameter is None
    assert test_object.parameter_name is None

    assert test_object.load(parameters) is True
    assert test_object.default_parameter == DEFAULT_VALUE
    assert test_object.parameter_name == DEFAULT_VALUE
    assert test_object.errors == []

    # test if default validator doesn't overwrite existing values
    test_object.default_parameter = 14
    test_object.parameter_name = 88
    assert test_object.load(parameters) is True
    assert test_object.default_parameter == 14
    assert test_object.parameter_name == 88
    assert test_object.errors == []


def test_required_validator() -> None:
    parameters: Namespace = command_line_to_namespace('')
    test_object = TestRequiredValidation()
    assert test_object.required_parameter is None
    assert test_object.default_required_parameter is None
    # assert test_object.required_default_parameter is None

    # nothing should be changed, if loading unsuccessful
    assert test_object.load(parameters) is False
    assert test_object.required_parameter is None
    assert test_object.default_required_parameter is None
    assert test_object.required_default_parameter is None
    assert test_object.errors != []

    # ignore validation on load
    assert test_object.load(attributes=parameters, validate=False) is True

    assert test_object.required_parameter is None
    assert test_object.default_required_parameter is None
    assert test_object.required_default_parameter is None

    parameters = command_line_to_namespace('--required-parameter=15')

    # ignore validation on load
    assert test_object.load(attributes=parameters) is True

    assert test_object.required_parameter == 15
    assert test_object.default_required_parameter == DEFAULT_VALUE
    assert test_object.required_default_parameter == DEFAULT_VALUE
