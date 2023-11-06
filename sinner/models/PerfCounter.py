import time
from types import TracebackType
from typing import Optional, Type


class PerfCounter:

    def __init__(self, ns_mode: bool = False):
        self.execution_time: float = 0
        self.ns_mode: bool = ns_mode

    def __enter__(self) -> 'PerfCounter':
        self.start_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
        self.end_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        self.execution_time = self.end_time - self.start_time

    def __float__(self) -> float:
        return float(self.execution_time)
