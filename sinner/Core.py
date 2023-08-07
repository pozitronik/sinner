#!/usr/bin/env python3
import warnings
from argparse import Namespace
from typing import List, Callable, Tuple

import os
import sys

from sinner.Status import Status, Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import delete_subdirectories, list_class_descendants, resolve_relative_path, get_app_dir, TEMP_DIRECTORY
from sinner.validators.AttributeLoader import Rules

# single thread doubles cuda performance - needs to be set before torch import
if any(arg.startswith('--execution-provider') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '1'
# reduce tensorflow log level
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

#
# if 'ROCMExecutionProvider' in parameters.execution_providers:
#     del torch

warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')
warnings.filterwarnings('ignore', category=UserWarning, module='torchvision')


class Core(Status):
    gui: bool
    target_path: str
    output_path: str
    frame_processor: List[str]
    temp_dir: str
    extract_frames: bool
    keep_frames: bool

    parameters: Namespace
    preview_processors: dict[str, BaseFrameProcessor]  # cached processors for gui
    preview_handlers: dict[str, BaseFrameHandler]  # cached handlers for gui
    _stop_flag: bool = False

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'gui',
                'default': False
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'valid': lambda: os.path.exists(self.target_path),
                'required': lambda: not self.gui,
                'help': 'Select the target file or the directory'
            },
            {
                'parameter': {'output', 'output-path'},
                'attribute': 'output_path',
                'default:': lambda: self.suggest_output_path(),
            },
            {
                'parameter': 'frame-processor',
                'default': ['FaceSwapper'],
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor'),
                'help': 'Select the frame processor from available processors'
            },
            {
                'parameter': 'temp-dir',
                'default': lambda: self.suggest_temp_dir(),
                'help': 'Select the directory for temporary files'
            },
            {
                'parameter': 'keep-frames',
                'default': False,
                'help': 'Keep temporary frames'
            }
        ]

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        self.preview_processors = {}
        super().__init__(parameters)
        if self.frame_processor and 'ResultProcessor' not in self.frame_processor:
            self.frame_processor.append('ResultProcessor')

    def run(self, set_progress: Callable[[int], None] | None = None) -> None:
        current_target_path = self.target_path
        temp_resources: List[str] = []  # list of temporary created resources
        for processor_name in self.frame_processor:
            current_processor = BaseFrameProcessor.create(processor_name, self.parameters, target_path=current_target_path, temp_dir=self.temp_dir)
            if current_processor.state.is_finished:
                self.update_status(f'Processing with {current_processor.state.processor_name} already done ({current_processor.state.processed_frames_count}/{current_processor.state.frames_count})')
            else:
                if current_processor.state.is_started:
                    self.update_status(f'Temp resources for this target already exists with {current_processor.state.processed_frames_count} frames processed, continue processing with {current_processor.state.processor_name}')

                current_processor.process(desc=processor_name, set_progress=set_progress)
                current_processor.release_resources()
            current_target_path = current_processor.state.path
            temp_resources.append(current_processor.state.path)

        if self.keep_frames is False:  # todo: add a final result check before deleting (keep frames if something wrong)
            self.update_status('Deleting temp resources')
            delete_subdirectories(self.temp_dir, temp_resources)

    def suggest_temp_dir(self) -> str:
        return self.temp_dir if self.temp_dir is not None else os.path.join(get_app_dir(), TEMP_DIRECTORY)

    #  returns list of all processed frames, starting from the original
    def get_frame(self, frame_number: int = 0, extractor_handler: BaseFrameHandler | None = None, processed: bool = False) -> List[Tuple[Frame, str]]:
        result: List[Tuple[Frame, str]] = []
        try:
            if extractor_handler is None:
                extractor_handler = BaseFrameProcessor.suggest_handler(self.target_path, self.parameters)
            _, frame, _ = extractor_handler.extract_frame(frame_number)
            result.append((frame, 'Original'))
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            return result
        if processed:  # return processed frame
            try:
                if 'ResultProcessor' in self.frame_processor:
                    self.frame_processor.remove('ResultProcessor')
                for processor_name in self.frame_processor:
                    if processor_name not in self.preview_processors:
                        self.preview_processors[processor_name] = BaseFrameProcessor.create(processor_name=processor_name, parameters=self.parameters)
                    self.preview_processors[processor_name].load(self.parameters)
                    frame = self.preview_processors[processor_name].process_frame(frame)
                    result.append((frame, processor_name))
            except Exception as exception:  # skip, if parameters is not enough for processor
                self.update_status(message=str(exception), mood=Mood.BAD)
                pass
        return result

    def stop(self) -> None:
        self._stop_flag = True

    def suggest_output_path(self) -> str:
        target_name, target_extension = os.path.splitext(os.path.basename(self.target_path))
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), 'result-' + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, 'result-' + target_name + target_extension)
        return self.output_path
