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

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'log', 'logfile'},
                'attribute': 'logfile',
                'valid': lambda: self.log_write(),
                'help': 'Path to the log file'
            },
            {
                'module_help': 'The status messaging module'
            }
        ]

    def update_status(self, message: str, caller: str | None = None, mood: Mood = Mood.GOOD, emoji: str | None = None) -> None:
        if emoji is None:
            emoji = self.emoji
        if caller is None:
            caller = self.__class__.__name__
        print(f'{emoji}{mood}{caller}: {message}{Back.RESET}{Fore.RESET}')
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
