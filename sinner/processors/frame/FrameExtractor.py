import os
from argparse import Namespace
from typing import Callable

from sinner.State import State
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
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

    def __init__(self, parameters: Namespace):
        super().__init__(parameters=parameters)

    def process(self, frames_handler: BaseFrameHandler, state: State, desc: str = 'Processing', set_progress: Callable[[int], None] | None = None) -> None:
        frames_handler.get_frames_paths(state.out_dir)[state.processed_frames_count:]

    def process_frame(self, frame: Frame) -> Frame:
        pass
