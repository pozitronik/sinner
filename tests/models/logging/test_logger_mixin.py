import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from sinner.models.logger.LoggerMixin import LoggerMixin
from sinner.models.logger.Mood import Mood


class TestLoggerMixin:
    @pytest.fixture
    def logger(self):
        class TestLogger(LoggerMixin):
            pass

        return TestLogger()

    def test_set_position(self):
        with patch('sys.stdout.write') as mock_write:
            LoggerMixin.set_position((5, 10))
            mock_write.assert_called_once_with("\033[5;10H")

    def test_set_position_negative(self):
        with patch('sys.stdout.write') as mock_write, \
                patch('shutil.get_terminal_size') as mock_get_terminal_size:
            mock_get_terminal_size.return_value = MagicMock(lines=24, columns=80)
            LoggerMixin.set_position((-1, -1))
            mock_write.assert_called_once_with("\033[23;79H")

    def test_restore_position(self):
        with patch('sys.stdout.write') as mock_write:
            LoggerMixin.restore_position((5, 10))
            mock_write.assert_called_once_with("\033[u")

    @pytest.mark.parametrize("encoding,expected", [
        ("utf-8", True),
        ("ascii", False),
    ])
    def test_is_emoji_supported(self, encoding, expected):
        with patch('locale.getpreferredencoding', return_value=encoding):
            assert LoggerMixin.is_emoji_supported() == expected

    def test_update_status(self, logger):
        logger.enable_emoji = True
        logger.emoji = "📢"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            logger.update_status("Test message", mood=Mood.GOOD)
            assert "📢" in fake_out.getvalue()
            assert "Test message" in fake_out.getvalue()
            assert logger.__class__.__name__ in fake_out.getvalue()

    def test_update_status_without_emoji(self, logger):
        logger.enable_emoji = False

        with patch('sys.stdout', new=StringIO()) as fake_out:
            logger.update_status("Test message", mood=Mood.BAD)
            assert "Test message" in fake_out.getvalue()
            assert logger.__class__.__name__ in fake_out.getvalue()

    def test_update_status_with_position(self, logger):
        with patch('sys.stdout.write') as mock_write:
            logger.update_status("Test message", position=(1, 1))
            assert mock_write.call_count == 3  # set_position, message, restore_position

    def test_update_status_with_custom_caller(self, logger):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            logger.update_status("Test message", caller="CustomCaller")
            assert "CustomCaller" in fake_out.getvalue()

    @pytest.mark.parametrize("mood", [Mood.GOOD, Mood.BAD, Mood.NEUTRAL])
    def test_update_status_moods(self, logger, mood):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            logger.update_status("Test message", mood=mood)
            assert str(mood) in fake_out.getvalue()
