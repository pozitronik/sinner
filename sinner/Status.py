import locale
import logging
import shutil
import sys
from enum import Enum

from colorama import Fore, Back

from sinner.validators.AttributeLoader import AttributeLoader, Rules


class Mood(Enum):
    GOOD = (0, f'{Fore.LIGHTWHITE_EX}{Back.BLACK}')
    BAD = (1, f'{Fore.BLACK}{Back.RED}')
    NEUTRAL = (2, f'{Fore.YELLOW}{Back.BLACK}')

    def __str__(self) -> str:
        return self.value[1]


class Status(AttributeLoader):
    logfile: str | None = None
    logger: logging.Logger | None = None
    emoji: str = '😈'
    enable_emoji: bool

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'log', 'logfile'},
                'attribute': 'logfile',
                'default': None,
                'valid': lambda attribute, value: self.init_logger(value),
                'help': 'Path to the log file'
            },
            {
                'parameter': {'enable-emoji'},
                'attribute': 'enable_emoji',
                'default': lambda: self.is_emoji_supported(),
                'help': 'Enable emojis in status messages'
            },
            {
                'module_help': 'The status messaging module'
            }
        ]

    @staticmethod
    def set_position(position: tuple[int, int] | None = None) -> None:
        if position is not None:
            y = position[0]
            x = position[1]
            if y < 0 or x < 0:
                terminal_size = shutil.get_terminal_size()
                lines, columns = terminal_size.lines, terminal_size.columns
                if y < 0:
                    y = lines - y
                if x < 0:
                    x = columns - x

            sys.stdout.write(f"\033[{y};{x}H")

    @staticmethod
    def restore_position(position: tuple[int, int] | None = None) -> None:
        if position is not None:
            sys.stdout.write("\033[u")

    @staticmethod
    def is_emoji_supported() -> bool:
        try:
            return locale.getpreferredencoding().lower() == "utf-8"
        except Exception:
            return False

    def update_status(self, message: str, caller: str | None = None, mood: Mood = Mood.GOOD, emoji: str | None = None, position: tuple[int, int] | None = None) -> None:
        """
        Print the specified status message
        :param message: the status message text
        :param caller: the caller class name, None to a current class name
        :param mood: the mood of the message (good, bad, neutral)
        :param emoji: prefix emoji. Note: emoji may be skipped, if not supported in the current terminal
        :param position: output position as (line, column). Negative values interprets as positions from the bottom/right
        side of the console. Skip to print status at the current cursor position.
        """
        if self.enable_emoji:
            if emoji is None:
                emoji = self.emoji
        else:
            emoji = ''
        if caller is None:
            caller = self.__class__.__name__
        self.set_position(position)
        sys.stdout.write(f'{emoji}{mood}{caller}: {message}{Back.RESET}{Fore.RESET}')
        if position is None:
            sys.stdout.write("\n")
        self.restore_position(position)
        log_level = logging.DEBUG
        if mood is Mood.GOOD:
            log_level = logging.INFO
        elif mood is Mood.BAD:
            log_level = logging.ERROR
        self.log(level=log_level, msg=f"{emoji}{caller}: {message}")

    def log(self, level: int = logging.INFO, msg: str = "") -> None:
        if self.logger:
            self.logger.log(level, msg)

    def init_logger(self, value: str) -> bool:
        try:
            if value and not self.logger:
                self.logger = logging.getLogger(__name__)
                self.logger.setLevel(logging.DEBUG)

                file_handler = logging.FileHandler(value, encoding='utf-8', mode='w')
                file_handler.setLevel(logging.DEBUG)

                formatter = logging.Formatter('%(levelname)s: %(message)s')
                file_handler.setFormatter(formatter)

                self.logger.addHandler(file_handler)
                #
                # logging.getLogger('PIL.PngImagePlugin').setLevel(logging.CRITICAL + 1)
                # logging.getLogger('PIL.PngImagePlugin').addHandler(logging.NullHandler())
            return True
        except Exception:
            pass
        return False
