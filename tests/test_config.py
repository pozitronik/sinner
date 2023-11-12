import random
import shutil

from sinner.Parameters import Parameters
from sinner.models.Config import Config
from sinner.processors.frame.DummyProcessor import DummyProcessor
from tests.constants import test_config, target_png, test_config_bak


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


def setup() -> None:
    shutil.copyfile(test_config_bak, test_config)  # restore from bak file


def test_save_config_value() -> None:
    params = Parameters(f'--ini="{test_config}"')
    config = Config(params.config_name)
    assert hasattr(params.parameters, 'test_save_value') is False
    random_value = random.Random().randint(1, 100)
    config.set_key('sinner', 'test_save_value', random_value)
    params = Parameters(f'--ini="{test_config}"')
    assert hasattr(params.parameters, 'test_save_value') is True
    assert int(params.parameters.test_save_value) == random_value
    config.set_key('sinner', 'test_save_value', None)
    params = Parameters(f'--ini="{test_config}"')
    assert hasattr(params.parameters, 'test_save_value') is False
    shutil.copyfile(test_config_bak, test_config)
