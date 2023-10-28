import time


class PerfCounter:

    def __init__(self):
        self.execution_time: float = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        self.execution_time = self.end_time - self.start_time

    def __float__(self):
        return float(self.execution_time)
