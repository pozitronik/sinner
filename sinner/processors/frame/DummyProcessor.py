from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame


class DummyProcessor(BaseFrameProcessor):

    def process_frame(self, temp_frame: Frame) -> Frame:
        return temp_frame