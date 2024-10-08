from collections import deque


class MovingAverage:
    def __init__(self, window_size: int = 0):
        self.window_size = window_size
        if window_size > 0:
            self.window: deque[float] = deque(maxlen=window_size)
        else:
            self.sum: float = 0
            self.count: int = 0

    def update(self, value: float) -> None:
        if self.window_size > 0:
            self.window.append(value)
        else:
            self.sum += value
            self.count += 1

    def get_average(self) -> float:
        if self.window_size > 0:
            return sum(self.window) / len(self.window) if self.window else 0
        else:
            return self.sum / self.count if self.count > 0 else 0

    def reset(self) -> None:
        if self.window_size > 0:
            self.window.clear()
        else:
            self.sum = 0
            self.count = 0
