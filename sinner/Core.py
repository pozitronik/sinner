#!/usr/bin/env python3
import warnings
from argparse import Namespace
from typing import List, Callable

import os
import sys

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.State import State
from sinner.typing import Frame
from sinner.utilities import is_image, is_video, delete_subdirectories, list_class_descendants, resolve_relative_path, get_app_dir, TEMP_DIRECTORY
from sinner.validators.AttributeLoader import AttributeLoader, Rules
from sinner.validators.LoaderException import LoadingException

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


class Core(AttributeLoader):
    target_path: str
    output_path: str
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
                'parameter': 'target-path',
                'required': True,
                'help': 'Select the target file or the directory'
            },
            {
                'parameter': 'output-path',
                'help': 'Select an output file or a directory'
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
                'default': self.suggest_handler(self.target_path).__class__.__name__,
                'choices': list_class_descendants(resolve_relative_path('handlers/frame'), 'BaseFrameHandler'),
                'help': 'Select the frame handler from available handlers'
            },
            {
                'parameter': 'temp-dir',
                'default': lambda: self.temp_dir if self.temp_dir is not None else os.path.join(os.path.dirname(self.target_path), get_app_dir(), TEMP_DIRECTORY),
                'help': 'Select the directory for temporary files'
            },
            {
                'parameter': 'extract_frames',
                'default': False,
                'help': 'Extract video frames before processing'
            },
            {
                'parameter': 'keep_frames',
                'default': False,
                'help': 'Keep temporary frames'
            }
        ]

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        if not self.load(self.parameters):
            raise LoadingException(self.errors)
        self.preview_processors = {}

    def run(self, set_progress: Callable[[int], None] | None = None) -> None:
        self._stop_flag = False
        current_target_path = self.target_path
        temp_resources: List[str] = []  # list of temporary created resources
        for processor_name in self.frame_processor:
            if self._stop_flag:  # todo: create a shared variable to stop processing
                continue
            current_handler = self.suggest_handler(current_target_path)
            state = State(parameters=self.parameters, temp_dir=self.temp_dir, frames_count=current_handler.fc)
            current_processor = BaseFrameProcessor.create(processor_name, self.parameters, state)
            current_processor.process(frames_handler=current_handler, desc=processor_name, extract_frames=self.extract_frames, set_progress=set_progress)
            current_target_path = state.out_dir
            temp_resources.append(state.out_dir)
            if not self.extract_frames:
                temp_resources.append(state.in_dir)
            current_processor.release_resources()

        final_handler = BaseFrameHandler.create(handler_name=self.frame_handler, target_path=self.target_path)
        if final_handler.result(from_dir=current_target_path, filename=self.output_path, fps=self.fps, audio_target=self.target_path if self.keep_audio else None) is True:
            if self.keep_frames is False:
                delete_subdirectories(self.temp_dir, temp_resources)
        else:
            raise Exception("Something went wrong while resulting frames")

    @staticmethod
    def suggest_handler(target_path: str) -> BaseFrameHandler:
        if os.path.isdir(target_path):
            return DirectoryHandler(target_path)
        if is_image(target_path):
            return ImageHandler(target_path)
        if is_video(target_path):
            return VideoHandler(target_path)
        raise NotImplementedError("The handler for current target type is not implemented")

    def get_frame(self, frame_number: int = 0, processed: bool = False) -> Frame | None:
        extractor_handler = self.suggest_handler(self.target_path)
        try:
            _, frame = extractor_handler.extract_frame(frame_number)
        except Exception:
            return None
        if processed:  # return processed frame
            state = State(parameters=self.parameters, frames_count=1)
            for processor_name in self.frame_processor:
                if processor_name not in self.preview_processors:
                    self.preview_processors[processor_name] = BaseFrameProcessor.create(processor_name=processor_name, parameters=self.parameters, state=state)
                frame = self.preview_processors[processor_name].process_frame(frame)
        return frame

    def change_source(self, data: str) -> bool:
        if data != '':
            self.source_path = data
            self.preview_processors.clear()
            return True
        return False

    def change_target(self, data: str) -> bool:
        if data != '':
            self.target_path = data
            self.preview_processors.clear()
            return True
        return False

    def stop(self) -> None:
        self._stop_flag = True
