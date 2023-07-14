#!/usr/bin/env python3
import warnings
from argparse import Namespace
from typing import List, Callable

import os
import sys

from sinner.Status import Status
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.State import State
from sinner.typing import Frame
from sinner.utilities import is_image, is_video, delete_subdirectories, list_class_descendants, resolve_relative_path, get_app_dir, TEMP_DIRECTORY
from sinner.validators.AttributeLoader import AttributeLoader, Rules

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


class Core(AttributeLoader, Status):
    target_path: str
    frame_processor: List[str]
    frame_handler: str
    temp_dir: str
    extract_frames: bool
    keep_frames: bool

    parameters: Namespace
    preview_processors: dict[str, BaseFrameProcessor]  # cached processors for gui
    _stop_flag: bool = False

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'valid': lambda: os.path.exists(self.target_path),
                'required': True,
                'help': 'Select the target file or the directory'
            },
            {
                'parameter': 'frame-processor',
                'default': ['FaceSwapper'],
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor'),
                'help': 'Select the frame processor from available processors'
            },
            {
                'parameter': 'frame-handler',
                'default': lambda: self.suggest_handler(self.parameters, self.target_path).__class__.__name__,
                'choices': list_class_descendants(resolve_relative_path('handlers/frame'), 'BaseFrameHandler'),
                'help': 'Select the frame handler from available handlers'
            },
            {
                'parameter': 'temp-dir',
                'default': lambda: self.suggest_temp_dir(),
                'help': 'Select the directory for temporary files'
            },
            {
                'parameter': 'extract-frames',
                'default': False,
                'help': 'Extract video frames before processing'
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

    def run(self, set_progress: Callable[[int], None] | None = None) -> None:
        self._stop_flag = False
        current_target_path = self.target_path
        temp_resources: List[str] = []  # list of temporary created resources
        current_processor: BaseFrameProcessor | None = None
        for processor_name in self.frame_processor:
            if self._stop_flag:  # todo: create a shared variable to stop processing
                continue
            current_handler = self.suggest_handler(self.parameters, current_target_path)
            state = State(parameters=self.parameters, target_path=current_target_path, temp_dir=self.temp_dir, frames_count=current_handler.fc, processor_name=processor_name)
            if state.is_finished:
                self.update_status(f'Processing with {state.processor_name} already done ({state.processed_frames_count}/{state.frames_count})')
            else:
                if state.is_started:
                    self.update_status(f'Temp resources for this target already exists with {state.processed_frames_count} frames processed, continue processing with {state.processor_name}')
                current_processor = BaseFrameProcessor.create(processor_name, self.parameters)
                current_processor.process(frames_handler=current_handler, state=state, desc=processor_name, extract_frames=self.extract_frames, set_progress=set_progress)
                current_processor.release_resources()
            current_target_path = state.out_dir
            temp_resources.append(state.out_dir)
            if self.extract_frames:
                temp_resources.append(state.in_dir)

        if current_processor is not None:
            final_handler = BaseFrameHandler.create(handler_name=self.frame_handler, parameters=self.parameters, target_path=self.target_path)
            if final_handler.result(from_dir=current_target_path, filename=current_processor.output_path, audio_target=self.target_path) is True:
                if self.keep_frames is False:
                    self.update_status('Deleting temp resources')
                    delete_subdirectories(self.temp_dir, temp_resources)
            else:
                raise Exception("Something went wrong while resulting frames")

    @staticmethod
    def suggest_handler(parameters: Namespace, target_path: str | None) -> BaseFrameHandler:
        if target_path is None:
            raise Exception("The target path is not set")
        if os.path.isdir(target_path):
            return DirectoryHandler(target_path, parameters)
        if is_image(target_path):
            return ImageHandler(target_path, parameters)
        if is_video(target_path):
            return VideoHandler(target_path, parameters)
        raise NotImplementedError("The handler for current target type is not implemented")

    def suggest_temp_dir(self) -> str:
        return self.temp_dir if self.temp_dir is not None else os.path.join(get_app_dir(), TEMP_DIRECTORY)

    def get_frame(self, frame_number: int = 0, processed: bool = False) -> Frame | None:
        extractor_handler = self.suggest_handler(self.parameters, self.target_path)
        try:
            _, frame = extractor_handler.extract_frame(frame_number)
        except Exception:
            return None
        if processed:  # return processed frame
            for processor_name in self.frame_processor:
                if processor_name not in self.preview_processors:
                    self.preview_processors[processor_name] = BaseFrameProcessor.create(processor_name=processor_name, parameters=self.parameters)
                self.preview_processors[processor_name].load(self.parameters)
                frame = self.preview_processors[processor_name].process_frame(frame)
        return frame

    def stop(self) -> None:
        self._stop_flag = True
