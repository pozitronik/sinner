import time


class PerfCounter:

    def __init__(self, ns_mode: bool = False):
        self.execution_time: float = 0
        self.ns_mode: bool = ns_mode

    def __enter__(self):
        self.start_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        self.execution_time = self.end_time - self.start_time

    def __float__(self):
        return float(self.execution_time)
