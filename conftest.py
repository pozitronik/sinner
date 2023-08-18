import os


def pytest_sessionstart(session):
    #  try to avoid tkl initialization errors while testing in GitHub CI
    if 'CI' in os.environ and 'DISPLAY' not in os.environ:
        os.environ.__setitem__('DISPLAY', ':1.0')
