from sinner.frame_buffers.BaseFrameBuffer import BaseFrameBuffer
from sinner.frame_buffers.MemFrameBuffer import MemFrameBuffer
from sinner.typing import NumeratedFrame


class FrameBufferManager:
    _frame_buffers: dict[str, BaseFrameBuffer] = {}
    _fbi: dict[int, str] = {}  # frame buffers index
    _fbn: dict[str, int] = {}  # frame buffers reverse index

    def __init__(self, named_order: list[str]):
        for i, name in enumerate(named_order):
            self._fbi[i] = name
            self._fbn[name] = i
            self._frame_buffers[name] = MemFrameBuffer()

    def get_buffer_by_index(self, index: int) -> BaseFrameBuffer | None:
        if index in self._fbi:
            return self._frame_buffers[self._fbi[index]]

    def first(self) -> BaseFrameBuffer | None:
        return self.get_buffer_by_index(0)

    @property
    def len(self) -> int:
        return len(self._fbi)

    @property
    def size(self) -> int:
        size_ = 0
        for index in self._fbi:
            size_ += self.get_buffer_by_index(index).size
        return size_

    def get(self, buffer_name: str) -> BaseFrameBuffer:
        if buffer_name in self._frame_buffers:
            return self._frame_buffers[buffer_name]
        raise Exception(f'Buffer {buffer_name} is not found')

    def next(self, buffer_name: str) -> BaseFrameBuffer | None:
        if buffer_name in self._fbn:
            return self.get_buffer_by_index(self._fbn[buffer_name] + 1)
        return None

    def pop(self, buffer_name: str) -> NumeratedFrame | None:
        return self.get(buffer_name).pop()

    def push(self, buffer_name: str, frame: NumeratedFrame) -> int:
        self.get(buffer_name).push(frame)
        return self.len

    def push_next(self, buffer_name: str, frame: NumeratedFrame) -> bool:
        next_buffer = self.next(buffer_name)
        if next_buffer is None:
            return False
        else:
            next_buffer.push(frame)
            return True
