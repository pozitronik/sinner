import subprocess
import sys
from argparse import Namespace

from sinner.Parameters import Parameters
from tests.validators.TestValidatedClass import TestParameterAliases, TestParameterAttributes


def test_init() -> None:
    params = Parameters.command_line_to_namespace('--key4 --key1=value1 --key2=value2 --key3 value3 value4 --key10')
    assert params.key1 == 'value1'
    assert params.key2 == 'value2'
    assert params.key3 == ['value3', 'value4']
    assert params.key4 is True
    assert params.key10 is True


def test_parameters_aliases_loading() -> None:
    test_object = TestParameterAliases()
    assert hasattr(test_object, 'param_one') is False
    assert hasattr(test_object, 'param_one') is False
    assert hasattr(test_object, 'param_three') is False
    parameters: Namespace = Parameters.command_line_to_namespace('--param-one=1 --param-two=sdf --param-three=cddd')
    test_object.load(parameters)
    assert test_object.param_one == 1
    assert test_object.param_two == 'sdf'
    assert test_object.param_three == 'cddd'

    parameters: Namespace = Parameters.command_line_to_namespace('--param1=100 --param2=qwe --param3=xdf')
    test_object.load(parameters)
    assert test_object.param_one == 100
    assert test_object.param_two == 'qwe'
    assert test_object.param_three == 'xdf'

    parameters: Namespace = Parameters.command_line_to_namespace('--p1=42 --p2=xxx --p3=pik')
    test_object.load(parameters)
    assert test_object.param_one == 42
    assert test_object.param_two == 'xxx'
    assert test_object.param_three == 'pik'


def test_attributes_loading() -> None:
    test_object = TestParameterAttributes()
    assert hasattr(test_object, 'param_one') is False
    assert hasattr(test_object, 'param_one') is False
    parameters: Namespace = Parameters.command_line_to_namespace('--param-one=1 --param-two=sdf')
    test_object.load(parameters)
    assert test_object.param_one == 1
    assert test_object.param_two == 'sdf'


# simulates a run with the real command-line to properly test how the parameters loader handle it
def test_real_command_line(monkeypatch) -> None:
    command_line = ["sin.py", "--param-one=1", "--param-two=sdf"]
    monkeypatch.setattr(sys, 'argv', command_line)
    test_object = TestParameterAttributes(Parameters().parameters)
    assert test_object.param_one == 1
    assert test_object.param_two == 'sdf'
