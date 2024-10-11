from enum import Enum
from colorama import Fore, Back


class Mood(Enum):
    GOOD = (0, f'{Fore.LIGHTWHITE_EX}{Back.BLACK}')
    BAD = (1, f'{Fore.BLACK}{Back.RED}')
    NEUTRAL = (2, f'{Fore.YELLOW}{Back.BLACK}')

    def __str__(self) -> str:
        return self.value[1]