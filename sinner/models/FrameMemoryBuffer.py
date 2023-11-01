import threading
from typing import Dict

from sinner.models.NumberedFrame import NumberedFrame


# Internal class, used to implement extracted frames buffering
class FrameMemoryBuffer:
    _frames: Dict[int, NumberedFrame] = {}  # prototype, List[NumberedFrame] is enough

    def add_frame(self, frame: NumberedFrame) -> int:
        with threading.Lock():
            self._frames[frame.number] = NumberedFrame
        return len(self._frames)

    def get_frame(self, index: int) -> NumberedFrame | None:
        frame = None
        if index in self._frames:
            frame = self._frames[index]
            self._discard(index)
        return frame

    def _discard(self, threshold_index: int) -> int:
        with threading.Lock():
            keys_to_discard = [key for key in self._frames if key <= threshold_index]
            for key in keys_to_discard:
                del self._frames[key]
        return len(self._frames)
