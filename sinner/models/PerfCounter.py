import time
from typing import Optional, Self, Dict, List, Any, Type


class PerfCounter:
    def __init__(self, name: str = "total", ns_mode: bool = False, enabled: bool = True, parent: Optional['PerfCounter'] = None):
        self.name: str = name
        self.execution_time: float = 0
        self.ns_mode: bool = ns_mode
        self.enabled: bool = enabled
        self.parent: Optional['PerfCounter'] = parent
        self.start_time: float = 0
        self.end_time: float = 0

        # Инициализируем только если счетчик включен
        if enabled:
            self.segments: Dict[str, float] = {}
            self.subsegments: Dict[str, Dict[str, float]] = {}
            # Для сохранения порядка сегментов
            self.segment_order: List[str] = []

    def __enter__(self) -> Self:
        # Всегда измеряем общее время
        self.start_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Any) -> None:
        # Всегда измеряем общее время
        self.end_time = time.perf_counter_ns() if self.ns_mode else time.perf_counter()
        self.execution_time = self.end_time - self.start_time

        # Если у нас есть родитель, обновляем его информацию
        if self.parent and self.enabled:
            self.parent.record_segment(self.name, self.execution_time)

    def segment(self, name: str) -> 'PerfCounter':
        """Create a timing segment - returns a noop counter if disabled"""
        if not self.enabled:
            return PerfCounter(name=name, enabled=False, ns_mode=self.ns_mode)

        # Добавляем новый сегмент в порядок выполнения
        if name not in self.segment_order:
            self.segment_order.append(name)

        segment_counter = PerfCounter(
            name=name,
            ns_mode=self.ns_mode,
            enabled=True,
            parent=self  # Устанавливаем текущий счетчик как родителя
        )
        return segment_counter

    def record_segment(self, name: str, duration: float) -> None:
        """Record a segment duration"""
        if self.enabled:
            self.segments[name] = duration
            # Добавляем в порядок, если его нет
            if name not in self.segment_order:
                self.segment_order.append(name)

    def record_subsegment(self, segment_name: str, subsegment_name: str, duration: float) -> None:
        """Record a subsegment duration"""
        if not self.enabled:
            return

        if segment_name not in self.subsegments:
            self.subsegments[segment_name] = {}
        self.subsegments[segment_name][subsegment_name] = duration

    def percentage(self, segment_name: str) -> float:
        """Return the percentage of total time spent in segment"""
        if not self.enabled or self.execution_time <= 0:
            return 0
        return (self.segments.get(segment_name, 0) / self.execution_time) * 100

    def subsegment_percentage(self, segment_name: str, subsegment_name: str) -> float:
        """Return the percentage of segment time spent in subsegment"""
        if not self.enabled:
            return 0
        segment_time = self.segments.get(segment_name, 0)
        if segment_time <= 0:
            return 0
        subsegment_time = self.subsegments.get(segment_name, {}).get(subsegment_name, 0)
        return (subsegment_time / segment_time) * 100

    def __str__(self) -> str:
        """Format timing information with percentages"""
        if not self.enabled:
            return f"{self.name}: {self.execution_time:.6f}s"

        # Вычисляем общее время из сегментов, если execution_time нулевое
        total_time = self.execution_time
        if total_time <= 0 and self.segments:
            total_time = sum(self.segments.values())

        result = [f"{self.name}: {total_time:.6f}s"]

        # Выводим сегменты в порядке их создания
        for name in self.segment_order:
            if name in self.segments:
                time_value = self.segments[name]
                # Используем actual_percentage для корректного отображения
                actual_percentage = (time_value / total_time * 100) if total_time > 0 else 0
                result.append(f"  {name}: {time_value:.6f}s ({actual_percentage:.2f}%)")

                # Добавляем подсегменты, если они есть
                if name in self.subsegments and self.subsegments[name]:
                    for sub_name, sub_time in sorted(self.subsegments[name].items()):
                        sub_percentage = self.subsegment_percentage(name, sub_name)
                        result.append(f"    {sub_name}: {sub_time:.6f}s ({sub_percentage:.2f}% of {name})")

        return "\n".join(result)
