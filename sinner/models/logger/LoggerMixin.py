import logging

from sinner.models.logger.Mood import Mood


class LoggerMixin:
    _logger: logging.Logger | None

    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger

    def update_status(self, message: str, caller: str | None = None, mood: Mood = Mood.GOOD, emoji: str | None = None, position: tuple[int, int] | None = None) -> None:
        pass

    def log(self, level: int = logging.INFO, msg: str = "") -> None:
        pass
