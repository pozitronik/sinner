import logging

from colorama import Back, Fore

from sinner.models.logger.LogDestination import LogDestination
from sinner.models.logger.Mood import Mood
from sinner.models.logger.SelectiveLogger import SelectiveLogger


class LoggerMixin:
    _logger: SelectiveLogger | logging.Logger | None
    enable_emoji: bool = False
    emoji: str

    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            logging.setLoggerClass(SelectiveLogger)
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger

    def update_status(self, message: str, caller: str | None = None, mood: Mood = Mood.GOOD, emoji: str | None = None) -> None:
        if self.enable_emoji:
            if emoji is None:
                emoji = self.emoji
        else:
            emoji = ''
        if caller is None:
            caller = self.__class__.__name__
        self.logger.info(msg=f'{emoji}{mood}{caller}: {message}{Back.RESET}{Fore.RESET}', destinations=LogDestination.STDOUT)

    def log(self, level: int = logging.INFO, msg: str = "") -> None:
        self.logger.log(level, msg)
