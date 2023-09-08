from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame


class DummyProcessor(BaseFrameProcessor):
    emoji: str = '🤪'

    def process_frame(self, frame: Frame) -> Frame:
        return frame
