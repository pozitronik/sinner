from sinner.Parameters import Parameters
from tests.constants import test_config


def test_ini() -> None:
    params = Parameters(f'--ini="{test_config}"').parameters
    assert params.test_key == 'test_value'


def test_ini_and_cmd_line() -> None:
    params = Parameters(f'--ini="{test_config}" --max-memory=28').parameters
    assert params.test_key == 'test_value'
    assert params.max_memory == '28'
    assert bool(params.many_faces) is True
