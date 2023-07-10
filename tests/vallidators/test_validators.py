import argparse
import shlex
from argparse import ArgumentParser, Namespace

from sinner.Parameters import Parameters
from tests.vallidators.TestValidatedClass import DEFAULT_VALUE, TestDefaultValidation, TestRequiredValidation, TestUntypedAttribute, TestEqualValueAttribute, TestInValueAttribute, TestLambdaValueAttribute


def command_line_to_namespace(cmd_params: str) -> Namespace:
    args_list = shlex.split(cmd_params)
    result = []
    sublist = []

    for item in args_list:
        if item.startswith('--'):
            if sublist:
                result.append(sublist)
                sublist = []
            sublist.append(item)
        else:
            sublist.append(item)
    if sublist:
        result.append(sublist)

    parser = ArgumentParser()
    for parameter in result:
        if len(parameter) > 2:
            parser.add_argument(parameter[0], nargs=argparse.REMAINDER)  # mark parameter as a list

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

    parameters = command_line_to_namespace('--required-parameter=test')
    assert test_object.load(attributes=parameters) is True
    assert test_object.required_parameter == 'test'
    assert test_object.default_required_parameter == DEFAULT_VALUE
    assert test_object.required_default_parameter == DEFAULT_VALUE

    #  trying to use integer value
    parameters = command_line_to_namespace('--required-parameter=test --default_required_parameter=100')
    assert test_object.load(attributes=parameters) is True
    assert test_object.required_parameter == 'test'
    assert test_object.default_required_parameter == 100
    assert test_object.required_default_parameter == DEFAULT_VALUE


def test_untyped_attribute() -> None:
    test_object = TestUntypedAttribute()
    parameters: Namespace = command_line_to_namespace('--untyped-attribute=value')
    assert test_object.load(attributes=parameters) is True
    assert test_object.untyped_attribute == 'value'


def test_equal_value_validator() -> None:
    test_object = TestEqualValueAttribute()
    assert test_object.int_attribute is None
    parameters: Namespace = command_line_to_namespace('--int_attribute=10')
    assert test_object.load(attributes=parameters) is True
    assert test_object.int_attribute == 10

    parameters: Namespace = command_line_to_namespace('--int_attribute=42')
    assert test_object.load(attributes=parameters) is False
    assert test_object.int_attribute == 10
    assert test_object.errors == [{'attribute': 'int_attribute', 'error': 'Value 42 is not equal to 10', 'module': '😈sinner'}]


def test_in_value_validator() -> None:
    test_object = TestInValueAttribute()
    assert test_object.in_list_attribute is None
    parameters: Namespace = command_line_to_namespace('--in_list_attribute=7')
    assert test_object.load(attributes=parameters) is True
    assert test_object.in_list_attribute == 7

    parameters: Namespace = command_line_to_namespace('--in_list_attribute=42')
    assert test_object.load(attributes=parameters) is True
    assert test_object.in_list_attribute == 42

    parameters: Namespace = command_line_to_namespace('--in_list_attribute=15')
    assert test_object.load(attributes=parameters) is False
    assert test_object.in_list_attribute == 42


def test_lambda_validator() -> None:
    test_object = TestLambdaValueAttribute()
    assert test_object.lambda_attribute is None
    parameters: Namespace = command_line_to_namespace('--lambda_attribute=7')
    assert test_object.load(attributes=parameters) is False
    assert test_object.lambda_attribute is None

    parameters: Namespace = command_line_to_namespace('--lambda_attribute=42')
    assert test_object.load(attributes=parameters) is True
    assert test_object.lambda_attribute == 42

    parameters: Namespace = command_line_to_namespace('--lambda_attribute=15')
    assert test_object.load(attributes=parameters) is False
    assert test_object.lambda_attribute == 42
