#!/usr/bin/env python3
import signal
import sys

from sinner.Benchmark import Benchmark
from sinner.Parameters import Parameters
from sinner.Preview import Preview
from sinner.Core import Core
from sinner.utilities import limit_resources

if __name__ == '__main__':
    if sys.version_info < (3, 10):
        raise Exception('Python version is not supported - please upgrade to 3.10 or higher.')
    signal.signal(signal.SIGINT, lambda signal_number, frame: quit())

    params = Parameters()
    limit_resources(params.max_memory)
    if params.gui:
        core = Core(parameters=params.parameters)
        preview = Preview(core)
        window = preview.show()
        window.mainloop()
    elif params.benchmark is True:
        Benchmark(parameters=params.parameters)
    else:
        Core(parameters=params.parameters).run()
