#!/usr/bin/env python3
import sys

from roop import core

if __name__ == '__main__':
    if sys.version_info < (3, 9):
        raise Exception('Python version is not supported - please upgrade to 3.9 or higher.')
    core.run()
