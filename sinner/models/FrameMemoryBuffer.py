from typing import Dict

from sinner.models.NumberedFrame import NumberedFrame


class FrameMemoryBuffer:
    def __init__(self, source_name: str, target_name: str) -> None:
        self.source_name = source_name
        self.target_name = target_name
        # In-memory storage structure, organized by source/target combinations
        self.frames: Dict[int, NumberedFrame] = {}

    def clean(self) -> None:
        self.frames.clear()

    def add_frame(self, frame: NumberedFrame) -> None:
        """Adds a frame to the in-memory buffer."""
        self.frames[frame.index] = frame

    def get_frame(self, frame_index: int, return_previous: bool = True) -> NumberedFrame | None:
        """Retrieves a frame by its ID from the in-memory buffer, if it exists."""
        result = self.frames.get(frame_index)
        if not result and return_previous:
            # Find the nearest previous frame index
            closest_prev_index = max((index for index in self.frames.keys() if index < frame_index), default=None)
            if closest_prev_index is not None:
                return self.frames[closest_prev_index]
        return result

    def has_frame(self, frame_index: int) -> bool:
        """Checks if a frame exists in the in-memory buffer."""
        return frame_index in self.frames
