class EOutOfRange(BaseException):
    index: int
    min: int
    max: int

    """ Requested index is out of range. """

    def __init__(self, index: int, min_: int, max_: int):
        self.index = index
        self.min = min_
        self.max = max_

    def __str__(self) -> str:
        return f"Requested index {self.index} is not in range [{self.min}:{self.max}]"
