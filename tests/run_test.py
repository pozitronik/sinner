# testing different run configurations
from sinner.Parameters import Parameters
from sinner.core import Core
from sinner.utilities import limit_resources


def test_one() -> None:
    params = Parameters()
    limit_resources(params.max_memory)
    core = Core(parameters=params.parameters)
    core.run()
