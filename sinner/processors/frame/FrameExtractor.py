import os
from argparse import Namespace

from sinner.State import State
from sinner.Status import Status
from sinner.typing import Frame
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor


class FrameExtractor(BaseFrameProcessor):
    emoji: str = '🏃'

    def rules(self) -> Rules:
        super().rules()
        return [
            {
                'module_help': 'This module extracts frames from video file as set of png images'
            }
        ]

    def __init__(self, parameters: Namespace) -> None:
        self.parameters = parameters
        Status.__init__(self, self.parameters)

    def configure_state(self, state: State) -> None:
        state.path = os.path.abspath(os.path.join(state.temp_dir, self.__class__.__name__, os.path.basename(state.target_path)))

    def process_frame(self, frame: Frame) -> Frame:
        return frame
