from dataclasses import dataclass, field

from sinner.typing import Frame


@dataclass(order=True)
class NumberedFrame:
    index: int
    frame: Frame = field(compare=False)
    name: str | None = field(compare=False, default=None)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, NumberedFrame):
            raise NotImplementedError
        return self.index == o.index
