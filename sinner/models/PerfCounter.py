import time
from datetime import datetime
from typing import Optional, Self

from sinner.utilities import get_mem_usage


class PerfCounter:
    def __init__(self, name: str = "total", ns_mode: bool = False, enabled: bool = True, track_memory: bool = False, track_timestamp: bool = False):
        self.name: str = name
        self.execution_time: float = 0
        self.ns_mode: bool = ns_mode
        self.enabled: bool = enabled
        self.track_memory: bool = track_memory and enabled  # Отключаем трекинг памяти, если счетчик отключен
        self.track_timestamp: bool = track_timestamp and enabled

        # Инициализируем только если счетчик включен
        if enabled:
            self.segments: dict[str, float] = {}
            self.subsegments: dict[str, dict[str, float]] = {}
            self.memory_start: tuple[float, float] = (0, 0)
            self.memory_end: tuple[float, float] = (0, 0)
            self.timestamp: Optional[float] = None

    def __enter__(self) -> Self:
        # Всегда измеряем общее время
        self.start_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()

        # Остальные измерения только при enabled=True
        if self.enabled:
            if self.track_timestamp:
                self.timestamp = time.time()
        if self.track_memory:
            self.memory_start = (get_mem_usage(), get_mem_usage('vms'))
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        # Всегда измеряем общее время
        self.end_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        self.execution_time = self.end_time - self.start_time

        # Остальные измерения только при enabled=True
        if self.enabled and self.track_memory:
            self.memory_end = (get_mem_usage(), get_mem_usage('vms'))

    def segment(self, name: str) -> 'PerfCounter':
        """Create a timing segment - returns a noop counter if disabled"""
        if not self.enabled:
            return PerfCounter(name=name, enabled=False, ns_mode=self.ns_mode)

        segment_counter = PerfCounter(
            name=name,
            ns_mode=self.ns_mode,
            enabled=True,
            track_memory=self.track_memory,
            track_timestamp=self.track_timestamp
        )
        return segment_counter

    def record_segment(self, name: str, duration: float) -> None:
        """Record a segment duration"""
        if self.enabled:
            self.segments[name] = duration

    def record_subsegment(self, segment_name: str, subsegment_name: str, duration: float) -> None:
        """Record a subsegment duration"""
        if not self.enabled:
            return

        if segment_name not in self.subsegments:
            self.subsegments[segment_name] = {}
        self.subsegments[segment_name][subsegment_name] = duration

    def percentage(self, segment_name: str) -> float:
        """Return the percentage of total time spent in segment"""
        if not self.enabled or self.execution_time == 0:
            return 0
        return (self.segments.get(segment_name, 0) / self.execution_time) * 100

    def subsegment_percentage(self, segment_name: str, subsegment_name: str) -> float:
        """Return the percentage of segment time spent in subsegment"""
        segment_time = self.segments.get(segment_name, 0)
        if segment_time == 0:
            return 0
        subsegment_time = self.subsegments.get(segment_name, {}).get(subsegment_name, 0)
        return (subsegment_time / segment_time) * 100

    def memory_usage_str(self) -> str:
        """Format memory usage information"""
        if not self.track_memory:
            return ""
        rss_diff = self.memory_end[0] - self.memory_start[0]
        vms_diff = self.memory_end[1] - self.memory_start[1]
        return f"Memory: {rss_diff:.2f}MB RSS, {vms_diff:.2f}MB VMS"

    def timestamp_str(self) -> str:
        """Format timestamp information"""
        if not self.track_timestamp or self.timestamp is None:
            return ""
        return f"Time: {datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"

    def __str__(self) -> str:
        """Format timing information with percentages"""
        if not self.enabled:
            return f"{self.name}: {self.execution_time:.6f}s"
        result = [f"{self.name}: {self.execution_time:.6f}s"]

        if self.track_timestamp and self.timestamp:
            result.append(f"  {self.timestamp_str()}")

        if self.track_memory:
            result.append(f"  {self.memory_usage_str()}")

        if self.segments:
            for name, time_value in sorted(self.segments.items()):
                result.append(f"  {name}: {time_value:.6f}s ({self.percentage(name):.2f}%)")

                # Add subsegments if they exist
                if name in self.subsegments:
                    for sub_name, sub_time in sorted(self.subsegments[name].items()):
                        sub_percentage = self.subsegment_percentage(name, sub_name)
                        result.append(f"    {sub_name}: {sub_time:.6f}s ({sub_percentage:.2f}% of {name})")

        return "\n".join(result)
