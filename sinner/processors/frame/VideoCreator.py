import os
from argparse import Namespace
from typing import Callable

from sinner.State import State
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.typing import Frame
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.utilities import is_absolute_path


class VideoCreator(BaseFrameProcessor):

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'output', 'output-path'},
                'attribute': 'output_path',
                'default': lambda: self.suggest_output_path(),
                'valid': lambda: is_absolute_path(self.output_path),
                'help': 'Select an output file or a directory'
            }
        ]

    def suggest_output_path(self) -> str:
        target_name, target_extension = os.path.splitext(os.path.basename(self.target_path))
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), 'result-' + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, 'result-' + target_name + target_extension)
        return self.output_path

    def __init__(self, parameters: Namespace):
        super().__init__(parameters=parameters)

    def process(self, frames: BaseFrameHandler, state: State, desc: str = 'Processing', set_progress: Callable[[int], None] | None = None) -> None:
        handler = VideoHandler(self.target_path, self.parameters)  # todo: output format should be set via parameters
        handler.result(from_dir=state.target_path, filename=self.output_path, audio_target=self.target_path)

    def process_frame(self, frame: Frame) -> Frame:
        return frame
