from enum import Enum


class Mood(Enum):
    GOOD = '😈'
    BAD = '👿'
    NEUTRAL = '😑'


class Status:

    def update_status(self, message: str, caller: str | None = None, mood: Mood = Mood.GOOD) -> None:
        if caller is None:
            caller = self.__class__.__name__
        print(f'{mood}{caller}: {message}')
