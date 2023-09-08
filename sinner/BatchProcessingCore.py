import shutil
from argparse import Namespace
from typing import List, Callable

import os

from sinner.Status import Status
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.utilities import list_class_descendants, resolve_relative_path
from sinner.validators.AttributeLoader import Rules


class BatchProcessingCore(Status):
    target_path: str
    output_path: str
    frame_processor: List[str]
    temp_dir: str
    extract_frames: bool
    keep_frames: bool

    parameters: Namespace

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'valid': lambda: os.path.exists(self.target_path),
                'help': 'Path to the target file or directory (depends on used frame processors set)'
            },
            {
                'parameter': {'output', 'output-path'},
                'attribute': 'output_path',
                'default:': lambda: self.suggest_output_path(),
                'help': 'Path to the resulting file or directory (depends on used frame processors set and target)'
            },
            {
                'parameter': {'frame-processor', 'processor', 'processors'},
                'attribute': 'frame_processor',
                'default': ['FaceSwapper'],
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor'),
                'help': 'The set of frame processors to handle the target'
            },
            {
                'parameter': 'keep-frames',
                'default': False,
                'help': 'Keep temporary frames after processing'
            },
            {
                'module_help': 'The batch processing handler'
            }
        ]

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        self.preview_processors = {}
        super().__init__(parameters)
        if self.frame_processor and 'ResultProcessor' not in self.frame_processor:
            self.frame_processor.append('ResultProcessor')

    def run(self) -> None:
        current_target_path = self.target_path
        temp_resources: List[str] = []  # list of temporary created resources
        for processor_name in self.frame_processor:
            current_processor = BaseFrameProcessor.create(processor_name, self.parameters, target_path=current_target_path)
            if current_processor.state.is_finished:
                self.update_status(f'Processing with {current_processor.state.processor_name} already done ({current_processor.state.processed_frames_count}/{current_processor.state.frames_count})')
            else:
                if current_processor.state.is_started:
                    self.update_status(f'Temp resources for this target already exists with {current_processor.state.processed_frames_count} frames processed, continue processing with {current_processor.state.processor_name}')

                current_processor.process(desc=processor_name)
                current_processor.release_resources()
            current_target_path = current_processor.state.path
            temp_resources.append(current_processor.state.path)

        if self.keep_frames is False:
            self.update_status('Deleting temp resources')
            for dir_path in temp_resources:
                shutil.rmtree(dir_path, ignore_errors=True)

    def suggest_output_path(self) -> str:
        target_name, target_extension = os.path.splitext(os.path.basename(self.target_path))
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), 'result-' + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, 'result-' + target_name + target_extension)
        return self.output_path
