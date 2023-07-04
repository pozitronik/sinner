#!/usr/bin/env python3
import warnings
from typing import List

import torch
import os
import sys
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.parameters import Parameters
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.state import State
from sinner.typing import Frame
from sinner.utilities import is_image, is_video, delete_subdirectories

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
    frames_handler: BaseFrameHandler

    def __init__(self, params: Parameters):
        self.params = params

    def run(self) -> None:
        current_target_path = self.params.target_path
        temp_resources: List[str] = []  # list of temporary created resources
        for processor_name in self.params.frame_processors:
            current_handler = self.suggest_handler(current_target_path)
            state = State(
                source_path=self.params.source_path,
                target_path=current_target_path,
                frames_count=current_handler.fc,
                temp_dir=self.params.temp_dir
            )
            current_processor = BaseFrameProcessor.create(processor_name, self.params, state)
            current_processor.process(frames_handler=current_handler, in_memory=self.params.in_memory, desc=processor_name)
            current_target_path = state.out_dir
            temp_resources.append(state.out_dir)
            if not self.params.in_memory:
                temp_resources.append(state.in_dir)
            self.release_resources()

        final_handler = BaseFrameHandler.create(handler_name=self.params.frame_handler, target_path=self.params.target_path)
        if final_handler.result(from_dir=current_target_path, filename=self.params.output_path, fps=self.params.fps, audio_target=self.params.target_path if self.params.keep_audio else None) is True:
            if self.params.keep_frames is False:
                delete_subdirectories(self.params.temp_dir, temp_resources)
        else:
            raise Exception("Something went wrong while resulting frames")

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.params.execution_providers:
            torch.cuda.empty_cache()

    @staticmethod
    def suggest_handler(target_path: str) -> BaseFrameHandler:
        if os.path.isdir(target_path):
            return DirectoryHandler(target_path)
        if is_image(target_path):
            return ImageHandler(target_path)
        if is_video(target_path):
            return VideoHandler(target_path)
        raise NotImplementedError("The handler for current target type is not implemented")

    def get_frame(self, frame_number: int = 0) -> Frame:
        extractor_handler = self.suggest_handler(self.params.target_path)
        frame = extractor_handler.extract_frame(frame_number)
        state = State(
            source_path=self.params.source_path,
            target_path=self.params.target_path,
            frames_count=1,
            temp_dir=self.params.temp_dir
        )
        for processor_name in self.params.frame_processors:
            current_processor = BaseFrameProcessor.create(processor_name=processor_name, parameters=self.params, state=state)
            frame = current_processor.process_frame(frame)
        return frame
