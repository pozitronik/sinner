import os
from argparse import Namespace
from typing import Callable

from sinner.Core import Core
from sinner.State import State
from sinner.Status import Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import Frame
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.utilities import is_absolute_path


class ResultProcessor(BaseFrameProcessor):
    source_path: str

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path',
            },
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
        prefix = 'result-' if self.source_path is None else os.path.splitext(os.path.basename(self.source_path))[0]+'-'
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), prefix + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, prefix + target_name + target_extension)
        return self.output_path

    def __init__(self, parameters: Namespace):
        super().__init__(parameters=parameters)

    def process(self, frames: BaseFrameHandler, state: State, desc: str = 'Processing', set_progress: Callable[[int], None] | None = None) -> None:
        handler = Core.suggest_handler(self.target_path, self.parameters)  # todo: output format should be set via parameters
        if state.target_path is not None:
            handler.result(from_dir=state.target_path, filename=self.output_path, audio_target=self.target_path)
        else:
            self.update_status('Target path is empty, ignoring', mood=Mood.BAD)

    def process_frame(self, frame: Frame) -> Frame:
        return frame
