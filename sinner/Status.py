from enum import Enum

from sinner.typing import UTF8
from sinner.validators.AttributeLoader import AttributeLoader, Rules


class Mood(Enum):
    GOOD = (0, '😈')
    BAD = (1, '👿')
    NEUTRAL = (2, '😑')

    def __str__(self) -> str:
        return self.value[1]


class Status(AttributeLoader):
    logfile: str

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'log', 'logfile'},
                'attribute': 'logfile',
                'valid': lambda: self.log_write(),
                'help': 'Path to the log file'
            },
        ]

    def update_status(self, message: str, caller: str | None = None, mood: Mood = Mood.GOOD) -> None:
        if caller is None:
            caller = self.__class__.__name__
        content = f'{mood}{caller}: {message}'
        print(content)
        self.log_write(content)

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
