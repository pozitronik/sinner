import sys

from sinner.frame_buffers.BaseFrameBuffer import BaseFrameBuffer
from sinner.typing import NumeratedFrame


class MemFrameBuffer(BaseFrameBuffer):
    _items: list[NumeratedFrame] = []

    def __init__(self, name: str):
        super().__init__(name)
        self._items: list[NumeratedFrame] = []

    def pop(self) -> NumeratedFrame | None:
        return None if self.len == 0 else self._items.pop()

    def push(self, frame: NumeratedFrame) -> int:
        self._items.append(frame)
        return self.len

    def load(self, frames: list[NumeratedFrame]) -> int:
        self._items = []
        self._items.extend(frames)
        return self.len

    @property
    def len(self) -> int:
        return len(self._items)

    @property
    def size(self) -> int:
        _size: int = 0
        for item in self._items:
            _size += sys.getsizeof(item)
        return _size