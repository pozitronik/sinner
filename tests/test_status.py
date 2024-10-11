from argparse import Namespace

import pytest
from colorama import Fore, Back

from sinner.Parameters import Parameters
from sinner.models.logger.Logger import Logger, Mood
from sinner.typing import UTF8
from sinner.validators.LoaderException import LoadingException
from tests.constants import test_logfile


def test_status(capsys) -> None:
    status = Logger(Namespace())

    status.update_status('test', 'self', Mood.BAD)
    captured = capsys.readouterr()
    captured = captured.out.strip()
    assert captured.find(f'{Fore.BLACK}{Back.RED}self: test{Back.RESET}{Fore.RESET}') != -1


def test_status_force_emoji() -> None:
    parameters: Namespace = Parameters(f'--log="{test_logfile}" --enable_emoji=1').parameters
    status = Logger(parameters=parameters)

    status.update_status('test', 'self', Mood.BAD)
    with open(test_logfile, encoding=UTF8) as file:
        actual_content = file.read()
    assert actual_content.find('😈self: test') != -1


def test_status_log() -> None:
    parameters: Namespace = Parameters(f'--log="{test_logfile}" --enable_emoji=0').parameters
    status = Logger(parameters=parameters)

    status.update_status('test', 'self', Mood.BAD)
    with open(test_logfile, encoding=UTF8) as file:
        actual_content = file.read()
    assert actual_content.find('self: test') != -1


def test_status_error() -> None:
    parameters: Namespace = Parameters(f'--log="/dev/random/incorrect:file\\path*?"').parameters
    with pytest.raises(LoadingException):
        assert Logger(parameters=parameters)
