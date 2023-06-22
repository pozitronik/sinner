#!/usr/bin/env python3

import os
import sys
from argparse import Namespace

from roop.handlers.video import BaseVideoHandler
from roop.handlers.video.CV2VideoHandler import CV2VideoHandler
from roop.parameters import suggest_max_memory, suggest_execution_providers, suggest_execution_threads, Parameters
from roop.processors.frame.FaceSwapper import FaceSwapper
from roop.state import State

# single thread doubles cuda performance - needs to be set before torch import
if any(arg.startswith('--execution-provider') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '1'
# reduce tensorflow log level
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import warnings
import platform
import signal
import shutil
import argparse
import torch
import tensorflow
import roop.metadata
from roop.utilities import clean_temp, update_status, move_temp

params: Parameters
video_handler: BaseVideoHandler
state: State
#
# if 'ROCMExecutionProvider' in params.execution_providers:
#     del torch

warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')
warnings.filterwarnings('ignore', category=UserWarning, module='torchvision')


def parse_args() -> Namespace:
    signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())
    program = argparse.ArgumentParser()
    program.add_argument('-s', '--source', help='select an source image', dest='source_path')
    program.add_argument('-t', '--target', help='select an target image or video', dest='target_path')
    program.add_argument('-o', '--output', help='select output file or directory', dest='output_path')
    program.add_argument('--frame-processor', help='pipeline of frame processors', dest='frame_processor')
    program.add_argument('--fps', help='set output video fps', dest='fps', default=None)
    program.add_argument('--keep-audio', help='keep original audio', dest='keep_audio', action='store_true', default=True)
    program.add_argument('--keep-frames', help='keep temporary frames', dest='keep_frames', action='store_true', default=False)
    program.add_argument('--many-faces', help='process every face', dest='many_faces', action='store_true', default=False)
    program.add_argument('--max-memory', help='maximum amount of RAM in GB', dest='max_memory', type=int, default=suggest_max_memory())
    program.add_argument('--execution-provider', help='execution provider', dest='execution_provider', default=['cpu'], choices=suggest_execution_providers(), nargs='+')
    program.add_argument('--execution-threads', help='number of execution threads', dest='execution_threads', type=int, default=suggest_execution_threads())
    program.add_argument('-v', '--version', action='version', version=f'{roop.metadata.name} {roop.metadata.version}')
    return program.parse_args()


def limit_resources() -> None:
    # prevent tensorflow memory leak
    gpus = tensorflow.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tensorflow.config.experimental.set_memory_growth(gpu, True)
    # limit memory usage
    if params.max_memory:
        memory = params.max_memory * 1024 ** 3
        if platform.system().lower() == 'darwin':
            memory = params.max_memory * 1024 ** 6
        if platform.system().lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def release_resources() -> None:
    if 'CUDAExecutionProvider' in params.execution_providers:
        torch.cuda.empty_cache()


def pre_check() -> bool:
    if sys.version_info < (3, 9):
        update_status('Python version is not supported - please upgrade to 3.9 or higher.')
        return False
    if not shutil.which('ffmpeg'):
        update_status('ffmpeg is not installed.')
        return False
    return True


def destroy() -> None:
    if state.is_finished():
        clean_temp(params.target_path, params.keep_frames)
    quit()


def run() -> None:
    roop.core.params = Parameters(parse_args())
    roop.core.state = State(roop.core.params)
    roop.core.state.create()
    if roop.core.state.is_multi_frame:  # picture to video swap
        roop.core.video_handler = CV2VideoHandler(roop.core.params.target_path)
        if not state.is_resumable():
            roop.core.video_handler.extract_frames(state.in_dir)

    swapper = FaceSwapper(params, roop.core.state)
    swapper.process()
    release_resources()

    if roop.core.state.is_multi_frame:  # picture to video swap
        roop.core.video_handler.create_video(roop.core.state.out_dir, roop.core.params.output_path, roop.core.params.fps, roop.core.params.target_path if roop.core.params.keep_audio else None)
    else:
        move_temp(roop.core.params.target_path, roop.core.params.output_path)
    roop.core.state.finish()
