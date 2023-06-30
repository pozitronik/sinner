#!/usr/bin/env python3

import warnings

import torch
import os
import sys
from roop.handlers.frame.BaseFrameHandler import BaseFrameHandler
from roop.handlers.frame.DirectoryHandler import DirectoryHandler
from roop.handlers.frame.ImageHandler import ImageHandler
from roop.handlers.frame.VideoHandler import VideoHandler
from roop.parameters import Parameters
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.state import State
from roop.utilities import is_image, is_video

# single thread doubles cuda performance - needs to be set before torch import
if any(arg.startswith('--execution-provider') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '1'
# reduce tensorflow log level
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

#
# if 'ROCMExecutionProvider' in params.execution_providers:
#     del torch

warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')
warnings.filterwarnings('ignore', category=UserWarning, module='torchvision')


class Core:
    params: Parameters
    state: State
    frames_handler: BaseFrameHandler

    def __init__(self, params: Parameters):
        self.params = params
        self.state = State(source_path=params.source_path, target_path=params.target_path, output_path=params.target_path, keep_frames=params.keep_frames, temp_dir=params.temp_dir)
        self.frames_handler = BaseFrameHandler.create(handler_name=params.frame_handler, target_path=params.target_path)  # todo: create handler right where it needed
        self.state.frames_count = self.frames_handler.fc

    def run(self) -> None:
        for processor_name in self.params.frame_processors:
            current_handler = self.suggest_handler(self.frames_handler)
            current_processor = BaseFrameProcessor.create(processor_name, self.params, self.state)
            current_processor.process(frames_handler=current_handler, in_memory=self.params.in_memory, desc=processor_name)
            self.release_resources()
            self.state.reload()  # todo reload only for next processor

        if self.frames_handler.result(from_dir=self.state.target_path, filename=self.params.output_path, fps=self.params.fps, audio_target=self.params.target_path if self.params.keep_audio else None) is True:
            self.state.finish()
        else:
            raise Exception("Something went wrong while resulting frame")

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.params.execution_providers:
            torch.cuda.empty_cache()

    def suggest_handler(self, default_handler: BaseFrameHandler) -> BaseFrameHandler:
        if os.path.isdir(self.state.target_path):
            return DirectoryHandler(self.state.target_path)
        if is_image(self.state.target_path):
            return ImageHandler(self.state.target_path)
        if is_video(self.state.target_path):
            return VideoHandler(self.state.target_path)
        return default_handler
