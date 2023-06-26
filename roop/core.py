#!/usr/bin/env python3

import warnings
import torch
import os
import sys
from roop.handlers.frames.BaseFramesHandler import BaseFramesHandler
from roop.parameters import Parameters
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.state import State

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
    frames_handler: BaseFramesHandler | None
    frame_processor: BaseFrameProcessor

    def __init__(self, params: Parameters, state: State, frame_processor: BaseFrameProcessor, frames_handler: BaseFramesHandler | None = None):
        self.params = params
        self.state = state
        self.frames_handler = frames_handler
        self.frames_handler.current_frame_index = state.processed_frames_count()
        self.frame_processor = frame_processor

    def run(self) -> None:
        self.frame_processor.process(frames_provider=self.frames_handler)
        self.release_resources()

        if self.frames_handler.result(self.state.out_dir, self.params.output_path, self.params.fps, self.params.target_path if self.params.keep_audio else None) is True:
            self.state.finish()
        else:
            raise Exception("Something went wrong while resulting frames")

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.params.execution_providers:
            torch.cuda.empty_cache()
