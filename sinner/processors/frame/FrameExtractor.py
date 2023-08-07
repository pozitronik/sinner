import os
from argparse import Namespace
from typing import Callable

from sinner.State import State
from sinner.Status import Status
from sinner.typing import Frame
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.utilities import is_video


class FrameExtractor(BaseFrameProcessor):

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'required': True,
                'valid': lambda attribute_name, attribute_value: attribute_value is not None and is_video(attribute_value),
                'help': 'Select the target file (image or video) or the directory'
            }
        ]

    def suggest_output_path(self) -> str:
        target_name, target_extension = os.path.splitext(os.path.basename(self.target_path))
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), 'extracted-' + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, 'extracted-' + target_name + target_extension)
        return self.output_path

    def __init__(self, parameters: Namespace, target_path: str, temp_dir: str) -> None:
        self.parameters = parameters
        Status.__init__(self, self.parameters)
        self.handler = self.suggest_handler(target_path, self.parameters)
        self.state = State(parameters=self.parameters, target_path=target_path, temp_dir=temp_dir, frames_count=self.handler.fc, processor_name=self.__class__.__name__)
        self.state.path = os.path.abspath(os.path.join(self.state.temp_dir, self.__class__.__name__, os.path.basename(target_path)))

    def process(self, desc: str = 'Processing', set_progress: Callable[[int], None] | None = None) -> None:
        self.handler.get_frames_paths(self.state.path, (self.state.processed_frames_count, None))

    def process_frame(self, frame: Frame) -> Frame:
        return frame
