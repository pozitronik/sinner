from enum import Enum


class Mood(Enum):
    GOOD = (0, '😈')
    BAD = (1, '👿')
    NEUTRAL = (2, '😑')

    def __str__(self):
        return self.value[1]


class Status:

    def update_status(self, message: str, caller: str | None = None, mood: Mood = Mood.GOOD) -> None:
        if caller is None:
            caller = self.__class__.__name__
        print(f'{mood}{caller}: {message}')
