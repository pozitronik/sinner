from argparse import Namespace

from colorama import Fore, Back

from sinner.Parameters import Parameters
from sinner.Status import Status, Mood


def test_status(capsys) -> None:
    status = Status(Namespace())

    status.update_status('test', 'self', Mood.BAD)
    captured = capsys.readouterr()
    captured = captured.out.strip()
    assert captured.find(f'{Fore.BLACK}{Back.RED}self: test{Back.RESET}{Fore.RESET}') != -1


def test_status_force_emoji(capsys) -> None:
    parameters: Namespace = Parameters(f'--enable_emoji=1').parameters
    status = Status(parameters=parameters)

    status.update_status('test', 'self', Mood.BAD)
    captured = capsys.readouterr()
    captured = captured.out.strip()
    assert captured.find('😈') != -1
