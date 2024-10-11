import pytest
import logging
from io import StringIO
from unittest.mock import patch
from sinner.models.logger.LoggerMixin import LoggerMixin
from sinner.models.logger.Mood import Mood
from sinner.models.logger.LogDestination import LogDestination
from colorama import Fore, Back


class TestClass(LoggerMixin):
    pass


@pytest.fixture
def test_instance():
    return TestClass()


@pytest.fixture
def stream():
    return StringIO()


@pytest.fixture
def test_instance_with_stream(test_instance, stream):
    test_instance.logger.stdout_handler.stream = stream
    return test_instance


def test_logger_initialization(test_instance):
    assert test_instance.logger is not None
    assert test_instance.logger.name == "TestClass"


def test_update_status_without_emoji(test_instance_with_stream, stream):
    test_instance_with_stream.update_status("Test message")
    assert f"{Fore.LIGHTWHITE_EX}{Back.BLACK}TestClass: Test message{Back.RESET}{Fore.RESET}" in stream.getvalue()


def test_update_status_with_emoji(test_instance_with_stream, stream):
    test_instance_with_stream.enable_emoji = True
    test_instance_with_stream.emoji = "🔧"
    test_instance_with_stream.update_status("Test with emoji")
    assert f"🔧{Fore.LIGHTWHITE_EX}{Back.BLACK}TestClass: Test with emoji{Back.RESET}{Fore.RESET}" in stream.getvalue()


@pytest.mark.parametrize("mood, expected_color", [
    (Mood.GOOD, f"{Fore.LIGHTWHITE_EX}{Back.BLACK}"),
    (Mood.BAD, f"{Fore.BLACK}{Back.RED}"),
    (Mood.NEUTRAL, f"{Fore.YELLOW}{Back.BLACK}")
])
def test_update_status_with_mood(test_instance_with_stream, stream, mood, expected_color):
    test_instance_with_stream.update_status("Mood test", mood=mood)
    expected_output = f"{expected_color}TestClass: Mood test{Back.RESET}{Fore.RESET}"
    assert expected_output in stream.getvalue()


def test_log_destination(test_instance):
    with patch('sinner.models.logger.SelectiveLogger.SelectiveLogger._log') as mock_log:
        test_instance.update_status("Test destination")
        mock_log.assert_called_with(
            logging.INFO,
            f'{Fore.LIGHTWHITE_EX}{Back.BLACK}TestClass: Test destination{Back.RESET}{Fore.RESET}',
            (),
            destinations=LogDestination.STDOUT,
        )


def test_custom_caller(test_instance_with_stream, stream):
    test_instance_with_stream.update_status("Custom caller test", caller="CustomCaller")
    assert f"{Fore.LIGHTWHITE_EX}{Back.BLACK}CustomCaller: Custom caller test{Back.RESET}{Fore.RESET}" in stream.getvalue()
