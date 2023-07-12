# testing different run configurations
import os.path

import pytest

from sinner.Parameters import Parameters
from sinner.Core import Core
from sinner.utilities import limit_resources
from sinner.validators.LoaderException import LoadingException
from tests.constants import target_png, source_jpg, target_mp4, source_target_png_result, source_target_mp4_result


def test_one() -> None:
    params = Parameters()
    limit_resources(params.max_memory)
    with pytest.raises(LoadingException):
        Core(parameters=params.parameters).run()  # target path is fucked up


def test_two() -> None:
    params = Parameters(f'--target_path="{target_png}" --source_path=no_such_file')
    limit_resources(params.max_memory)
    with pytest.raises(LoadingException):
        Core(parameters=params.parameters).run()  # source path is fucked up


def test_three() -> None:
    if os.path.exists(source_target_png_result):
        os.remove(source_target_png_result)
    assert os.path.exists(source_target_png_result) is False
    params = Parameters(f'--target_path="{target_png}" --source_path="{source_jpg}"')
    limit_resources(params.max_memory)
    Core(parameters=params.parameters).run()
    assert os.path.exists(source_target_png_result) is True


def test_four() -> None:
    if os.path.exists(source_target_mp4_result):
        os.remove(source_target_mp4_result)
    assert os.path.exists(source_target_mp4_result) is False
    params = Parameters(f'--target_path="{target_mp4}" --source_path="{source_jpg}"')
    limit_resources(params.max_memory)
    Core(parameters=params.parameters).run()
    assert os.path.exists(source_target_mp4_result) is True
