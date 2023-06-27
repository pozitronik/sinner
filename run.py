#!/usr/bin/env python3
import signal
import sys

from roop.core import Core
from roop.parameters import Parameters
from roop.utilities import limit_resources

if __name__ == '__main__':
    if sys.version_info < (3, 10):
        raise Exception('Python version is not supported - please upgrade to 3.10 or higher.')
    signal.signal(signal.SIGINT, lambda signal_number, frame: quit())

    params = Parameters()
    limit_resources(params.max_memory)
    core = Core(params=params)
    core.run()
