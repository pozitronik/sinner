from enum import Flag, auto


class LogDestination(Flag):
    STDOUT = auto()
    FILE = auto()
    BOTH = STDOUT | FILE
