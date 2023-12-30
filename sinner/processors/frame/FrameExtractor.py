import os
from argparse import Namespace

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.models.State import State
from sinner.Status import Status
from sinner.typing import Frame
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor


class FrameExtractor(BaseFrameProcessor):
    emoji: str = '🏃'
    self_processing: bool = True

    def rules(self) -> Rules:
        return [
            {
                'module_help': 'This module extracts frames from video file as set of png images'
            }
        ]

    def __init__(self, parameters: Namespace) -> None:
        self.parameters = parameters
        Status.__init__(self, self.parameters)

    def configure_state(self, state: State) -> None:
        state.path = os.path.abspath(os.path.join(state.temp_dir, self.__class__.__name__, str(os.path.basename(str(state.target_path)))))

    def process_frame(self, frame: Frame) -> Frame:
        return frame

    def process(self, handler: BaseFrameHandler, state: State) -> None:
        handler.get_frames_paths(path=state.path, frames_range=(state.processed_frames_count, None))
