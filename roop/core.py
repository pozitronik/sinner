#!/usr/bin/env python3

import warnings
import torch
import os
import sys
from roop.handlers.video.BaseVideoHandler import BaseVideoHandler
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
    video_handler: BaseVideoHandler | None
    frame_processor: BaseFrameProcessor

    def __init__(self, params: Parameters, state: State, frame_processor: BaseFrameProcessor, video_handler: BaseVideoHandler | None):
        self.params = params
        self.state = state
        self.video_handler = video_handler
        self.frame_processor = frame_processor

    def run(self) -> None:
        # if self.state.is_multi_frame:  # picture to video swap
            # if not self.params.less_files and not self.state.is_resumable():
            #     self.video_handler.extract_frames(self.state.in_dir)

        self.frame_processor.process(frames_provider=self.video_handler)
        self.release_resources()

        if self.state.is_multi_frame:  # picture to video swap
            self.video_handler.create_video(self.state.out_dir, self.params.output_path, self.params.fps, self.params.target_path if self.params.keep_audio else None)
        else:
            pass  # move_temp(params.target_path, params.output_path) # check this
        self.state.finish()

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.params.execution_providers:
            torch.cuda.empty_cache()
