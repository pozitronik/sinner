from dataclasses import dataclass, field

from sinner.typing import Frame


@dataclass(order=True)
class NumberedFrame:
    number: int
    frame: Frame = field(compare=False)
    name: str | None = field(compare=False, default=None)
    frame_time: float | None = field(compare=False, default=None)

    def __eq__(self, o: 'NumberedFrame') -> bool:
        return self.number == o.number
