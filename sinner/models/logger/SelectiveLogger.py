import logging
import sys

from sinner.models.logger.LogDestination import LogDestination
from sinner.models.logger.SelectiveFilter import SelectiveFilter


class SelectiveLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET, file_path='app.log'):
        super().__init__(name, level)

        # Настройка обработчика для stdout
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.stdout_handler.addFilter(SelectiveFilter(LogDestination.STDOUT))
        self.addHandler(self.stdout_handler)

        # Настройка обработчика для файла
        self.file_handler = logging.FileHandler(file_path, encoding='utf-8', mode='w')
        self.file_handler.addFilter(SelectiveFilter(LogDestination.FILE))
        self.addHandler(self.file_handler)

        self.stdout_handler.setFormatter(logging.Formatter('%(message)s'))
        self.file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s: %(message)s'))

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, destinations=LogDestination.BOTH):
        if extra is None:
            extra = {}
        extra['destinations'] = destinations
        super()._log(level, msg, args, exc_info, extra, stack_info)

    def debug(self, msg, *args, **kwargs):
        destinations = kwargs.pop('destinations', LogDestination.BOTH)
        self._log(logging.DEBUG, msg, args, destinations=destinations, **kwargs)

    def info(self, msg, *args, **kwargs):
        destinations = kwargs.pop('destinations', LogDestination.BOTH)
        self._log(logging.INFO, msg, args, destinations=destinations, **kwargs)

    def warning(self, msg, *args, **kwargs):
        destinations = kwargs.pop('destinations', LogDestination.BOTH)
        self._log(logging.WARNING, msg, args, destinations=destinations, **kwargs)

    def error(self, msg, *args, **kwargs):
        destinations = kwargs.pop('destinations', LogDestination.BOTH)
        self._log(logging.ERROR, msg, args, destinations=destinations, **kwargs)

    def critical(self, msg, *args, **kwargs):
        destinations = kwargs.pop('destinations', LogDestination.BOTH)
        self._log(logging.CRITICAL, msg, args, destinations=destinations, **kwargs)
