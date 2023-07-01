from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.typing import Frame


class DummyProcessor(BaseFrameProcessor):

    def process_frame(self, temp_frame: Frame) -> Frame:
        return temp_frame
