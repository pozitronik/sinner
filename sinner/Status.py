import locale
import shutil
import sys
from enum import Enum

from colorama import Fore, Back

from sinner.typing import UTF8
from sinner.validators.AttributeLoader import AttributeLoader, Rules


class Mood(Enum):
    GOOD = (0, f'{Fore.LIGHTWHITE_EX}{Back.BLACK}')
    BAD = (1, f'{Fore.BLACK}{Back.RED}')
    NEUTRAL = (2, f'{Fore.YELLOW}{Back.BLACK}')

    def __str__(self) -> str:
        return self.value[1]


class Status(AttributeLoader):
    logfile: str
    emoji: str = '😈'
    enable_emoji: bool

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'log', 'logfile'},
                'attribute': 'logfile',
                'valid': lambda: self.log_write(),
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
        self.log_write(f'{emoji}{caller}: {message}')

    def log_write(self, content: str | None = None) -> bool:
        try:
            if self.logfile:
                with open(self.logfile, "w", encoding=UTF8) as log:
                    if content:
                        log.write(content)
                    return True
        except Exception:
            pass
        return False
