# testing different run configurations
import pytest

from sinner.Parameters import Parameters
from sinner.Core import Core
from sinner.utilities import limit_resources
from sinner.validators.LoaderException import LoadingException
from tests.constants import target_png


def test_one() -> None:
    params = Parameters()
    limit_resources(params.max_memory)
    with pytest.raises(LoadingException):
        Core(parameters=params.parameters).run()


def test_two() -> None:
    params = Parameters(f'--target_path={target_png}')
    limit_resources(params.max_memory)
    Core(parameters=params.parameters).run()

