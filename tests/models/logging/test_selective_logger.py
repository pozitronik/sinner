import pytest
import logging
from io import StringIO
from unittest.mock import patch
from sinner.models.logger.SelectiveLogger import SelectiveLogger
from sinner.models.logger.LogDestination import LogDestination
from sinner.typing import UTF8
from tests.constants import test_logfile


@pytest.fixture
def logger():
    return SelectiveLogger("test_logger", level=logging.DEBUG, file_path=test_logfile)


@pytest.fixture
def stream():
    return StringIO()


@pytest.fixture
def logger_with_stream(logger, stream):
    logger.stdout_handler.stream = stream
    return logger


def test_log_to_stdout(logger_with_stream, stream):
    logger_with_stream.info("Test message", destinations=LogDestination.STDOUT)
    assert "Test message" in stream.getvalue()


def test_log_to_file(logger):
    with open(test_logfile, encoding=UTF8) as file:
        logger.info("File message", destinations=LogDestination.FILE)
        assert "File message" in file.read()


def test_log_to_both(logger_with_stream, stream):
    with open(test_logfile, encoding=UTF8) as file:
        logger_with_stream.info("Both message", destinations=LogDestination.BOTH)
        assert "Both message" in stream.getvalue()
        assert "Both message" in file.read()


@pytest.mark.parametrize("level", [
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL
])
def test_log_levels(logger_with_stream, stream, level):
    logger_with_stream.log(level, f"Test {logging.getLevelName(level)}")
    assert logging.getLevelName(level) in stream.getvalue()
