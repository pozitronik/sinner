from argparse import Namespace
from sinner.Status import Status
from sinner.typing import Frame
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor


class FrameExtractor(BaseFrameProcessor):
    emoji: str = '🏃'

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'module_help': 'This module extracts frames from video file as set of png images'
            }
        ]

    def __init__(self, parameters: Namespace) -> None:
        self.parameters = parameters
        Status.__init__(self, self.parameters)
        # self.handler = self.suggest_handler(target_path, self.parameters)
        # self.state = State(parameters=self.parameters, target_path=target_path, temp_dir=self.temp_dir, frames_count=self.handler.fc, processor_name=self.__class__.__name__)
        # self.state.path = os.path.abspath(os.path.join(self.state.temp_dir, self.__class__.__name__, os.path.basename(target_path)))

    def process_frame(self, frame: Frame) -> Frame:
        return frame
