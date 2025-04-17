import time
from typing import Optional, Self, Dict, List, Any, Type


class TimingSegment:
    """Lightweight timing segment for PerfCounter"""

    def __init__(self, parent: 'PerfCounter', name: str, enabled: bool = True):
        self.parent = parent
        self.name = name
        self.ns_mode = parent.ns_mode if parent else False
        self.enabled = enabled
        self.start_time = 0

    def __enter__(self) -> Self:
        self.start_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Any) -> None:
        if not self.enabled:
            return

        end_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        duration = end_time - self.start_time
        self.parent.record_segment(self.name, duration)


class PerfCounter:
    def __init__(self, name: str = "total", ns_mode: bool = False, collect_stats: bool = True):
        self.name: str = name
        self.execution_time: float = 0
        self.ns_mode: bool = ns_mode
        self.collect_stats: bool = collect_stats
        self.start_time: float = 0
        self.end_time: float = 0

        self.segments: Dict[str, float] = {}
        self.subsegments: Dict[str, Dict[str, float]] = {}
        # For preserving segment creation order
        self.segment_order: List[str] = []

    def __enter__(self) -> Self:
        # Always measure total time
        self.start_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Any) -> None:
        # Always measure total time
        self.end_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        self.execution_time = self.end_time - self.start_time

    def _add_to_segment_order(self, name: str) -> None:
        """Add segment name to order list if not already present"""
        if name not in self.segment_order:
            self.segment_order.append(name)

    def segment(self, name: str) -> TimingSegment:
        """Create a timing segment - returns a noop segment if disabled"""
        if not self.collect_stats:
            return TimingSegment(self, name, enabled=False)

        self._add_to_segment_order(name)
        return TimingSegment(self, name)

    def record_segment(self, name: str, duration: float) -> None:
        """Record a segment duration"""
        if self.collect_stats:
            self.segments[name] = duration
            self._add_to_segment_order(name)

    def record_subsegment(self, segment_name: str, subsegment_name: str, duration: float) -> None:
        """Record a subsegment duration"""
        if not self.collect_stats:
            return

        if segment_name not in self.subsegments:
            self.subsegments[segment_name] = {}
        self.subsegments[segment_name][subsegment_name] = duration

    def percentage(self, segment_name: str, total_time: Optional[float] = None) -> float:
        """Return the percentage of total time spent in segment

        Args:
            segment_name: Name of the segment
            total_time: Optional total time to use instead of execution_time
        """
        if not self.collect_stats:
            return 0

        # Use provided total_time or execution_time
        used_total = total_time if total_time is not None else self.execution_time
        if used_total <= 0:
            return 0

        return (self.segments.get(segment_name, 0) / used_total) * 100

    def subsegment_percentage(self, segment_name: str, subsegment_name: str) -> float:
        """Return the percentage of segment time spent in subsegment"""
        if not self.collect_stats:
            return 0
        segment_time = self.segments.get(segment_name, 0)
        if segment_time <= 0:
            return 0
        subsegment_time = self.subsegments.get(segment_name, {}).get(subsegment_name, 0)
        return (subsegment_time / segment_time) * 100

    def __str__(self) -> str:
        """Format timing information with percentages"""
        unit = "ns" if self.ns_mode else "s"
        if not self.collect_stats:
            return f"{self.name}: {self.execution_time:.6f}{unit}"

        # Calculate total time from segments if execution_time is zero (called before context closure)
        total_time = self.execution_time
        if total_time <= 0 and self.segments:
            total_time = sum(self.segments.values())

        result = [f"{self.name}: {total_time:.6f}{unit}"]

        # Output segments in order of creation
        for name in self.segment_order:
            if name in self.segments:
                result.append(f"  {name}: {self.segments[name]:.6f}{unit} ({self.percentage(name, total_time):.2f}%)")

                # Add subsegments if they exist
                if name in self.subsegments and self.subsegments[name]:
                    for sub_name, sub_time in sorted(self.subsegments[name].items()):
                        sub_percentage = self.subsegment_percentage(name, sub_name)
                        result.append(f"    {sub_name}: {sub_time:.6f}{unit} ({sub_percentage:.2f}% of {name})")

        return "\n".join(result)
