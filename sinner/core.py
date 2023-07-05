#!/usr/bin/env python3
import warnings
from typing import List, Callable

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
    preview_processors: dict[str, BaseFrameProcessor]  # cached processors for preview
    _stop_flag: bool = False

    def __init__(self, params: Parameters):
        self.params = params
        self.preview_processors = {}

    def run(self, set_progress: Callable[[int], None] | None = None) -> None:
        self._stop_flag = False
        current_target_path = self.params.target_path
        temp_resources: List[str] = []  # list of temporary created resources
        for processor_name in self.params.frame_processors:
            if self._stop_flag:  # todo: create a shared variable to stop processing
                continue
            current_handler = self.suggest_handler(current_target_path)
            state = State(
                source_path=self.params.source_path,
                target_path=current_target_path,
                frames_count=current_handler.fc,
                temp_dir=self.params.temp_dir
            )
            current_processor = BaseFrameProcessor.create(processor_name, self.params, state)
            current_processor.process(frames_handler=current_handler, in_memory=self.params.in_memory, desc=processor_name, set_progress=set_progress)
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

    def get_frame(self, frame_number: int = 0, processed: bool = False) -> Frame:
        extractor_handler = self.suggest_handler(self.params.target_path)
        _, frame = extractor_handler.extract_frame(frame_number)
        if processed:  # return processed frame
            state = State(
                source_path=self.params.source_path,
                target_path=self.params.target_path,
                frames_count=1,
                temp_dir=self.params.temp_dir
            )
            for processor_name in self.params.frame_processors:
                if processor_name not in self.preview_processors:
                    self.preview_processors[processor_name] = BaseFrameProcessor.create(processor_name=processor_name, parameters=self.params, state=state)
                frame = self.preview_processors[processor_name].process_frame(frame)
        return frame

    def change_source(self, data: str) -> bool:
        if data != '':
            self.params.source_path = data
            self.preview_processors.clear()
            return True
        return False

    def change_target(self, data: str) -> bool:
        if data != '':
            self.params.target_path = data
            self.preview_processors.clear()
            return True
        return False

    def stop(self) -> None:
        self._stop_flag = True
