import random

from sinner.Parameters import Parameters
from sinner.processors.frame.DummyProcessor import DummyProcessor
from tests.constants import test_config, target_png


def test_ini() -> None:
    params = Parameters(f'--ini="{test_config}"').parameters
    assert params.test_key == 'test_value'


def test_ini_and_cmd_line() -> None:
    params = Parameters(f'--ini="{test_config}" --max-memory=28').parameters
    assert params.test_key == 'test_value'
    assert params.max_memory == '28'
    assert bool(params.many_faces) is True


def test_module_parameters() -> None:
    params = Parameters(f'--ini="{test_config}"').module_parameters('TestModule')
    assert params.module_test_key == 'module_test_value'


def test_module_and_global_parameters() -> None:
    params = Parameters(f'--ini="{test_config}" --frame-processor DummyProcessor --target-path="{target_png}"').parameters
    assert params.many_faces == 'true'
    test_module = DummyProcessor(parameters=params)
    assert test_module.parameters.many_faces == 'false'


def test_save_config_value() -> None:
    config = Parameters(f'--ini="{test_config}"')
    assert hasattr(config.parameters, 'test_save_value') is False
    random_value = random.Random().randint(1, 100)
    config.set_module_parameter('sinner', 'test_save_value', random_value)
    config = Parameters(f'--ini="{test_config}"')
    assert hasattr(config.parameters, 'test_save_value') is True
    assert int(config.parameters.test_save_value) == random_value
    config.set_module_parameter('sinner', 'test_save_value', None)
    config = Parameters(f'--ini="{test_config}"')
    assert hasattr(config.parameters, 'test_save_value') is False
