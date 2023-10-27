from dataclasses import dataclass, field

from sinner.typing import Frame


@dataclass(order=True)
class NumberedFrame:
    number: int
    frame: Frame = field(compare=False)
    name: str | None = None

    def __eq__(self, o: 'NumberedFrame') -> bool:
        if self.name and o.name:
            return self.name is o.name
        return self.number == o.number
