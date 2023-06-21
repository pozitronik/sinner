#!/usr/bin/env python3

import os
import sys
from argparse import Namespace

from roop.ffmpeg import FFMPEG
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
from roop.utilities import clean_temp, create_temp, update_status, move_temp

params: Parameters
ffmpeg: FFMPEG
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


"""
def start() -> None:
    for frame_processor in get_frame_processors_modules(Params.frame_processors):
        if not frame_processor.pre_start():
            return
    # process image to image
    if has_image_extension(Params.target_path):
        if predict_image(Params.target_path):
            destroy()
        shutil.copy2(Params.target_path, Params.output_path)
        for frame_processor in get_frame_processors_modules(Params.frame_processors):
            update_status('Progressing...', frame_processor.NAME)
            frame_processor.process_image(Params.source_path, Params.output_path, Params.output_path)
            release_resources()
        if is_image(Params.target_path):
            update_status('Processing to image succeed!')
        else:
            update_status('Processing to image failed!')
        return
    # process image to videos
    if predict_video(Params.target_path):
        destroy()
    if state.is_resumable(Params.target_path):
        update_status(f'Temp resources for this target already exists with {state.processed_frames_count(Params.target_path)} frames processed, continue processing...')
    else:
        update_status('Creating temp resources...')
        create_temp(Params.target_path)
        update_status('Extracting frames...')
        extract_frames(Params.target_path)
    temp_frame_paths = get_temp_frame_paths(Params.target_path)
    for frame_processor in get_frame_processors_modules(Params.frame_processors):
        update_status('Progressing...', frame_processor.NAME)
        frame_processor.process_video(Params.source_path, temp_frame_paths)
        release_resources()
    # handles fps
    if Params.keep_fps:
        update_status('Detecting fps...')
        fps = detect_fps(Params.target_path)
        update_status(f'Creating video with {fps} fps...')
        create_video(Params.target_path, fps)
    else:
        update_status('Creating video with 30.0 fps...')
        create_video(Params.target_path)
    # handle audio
    if Params.keep_audio:
        if Params.keep_fps:
            update_status('Restoring audio...')
        else:
            update_status('Restoring audio might cause issues as fps are not kept...')
        restore_audio(Params.target_path, Params.output_path)
    else:
        move_temp(Params.target_path, Params.output_path)
    # clean and validate
    clean_temp(Params.target_path)
    if is_video(Params.target_path):
        update_status('Processing to video succeed!')
    else:
        update_status('Processing to video failed!')
"""


def destroy() -> None:
    if state.is_finished():
        clean_temp(params.target_path, params.keep_frames)
    quit()


def run() -> None:
    roop.core.params = Parameters(parse_args())
    roop.core.ffmpeg = FFMPEG(roop.core.params)
    roop.core.state = State(roop.core.params)
    if not state.is_resumable():
        update_status('Creating temp resources...')
        create_temp(roop.core.state.target_path)
        update_status('Extracting frames...')
        ffmpeg.extract_frames()

    swapper = FaceSwapper(params, roop.core.state)
    swapper.process()
    release_resources()

    # handles fps
    ffmpeg.create_video(roop.core.params.fps)
    # handle audio
    if roop.core.params.keep_audio:
        ffmpeg.restore_audio(roop.core.params.output_path)
    else:
        move_temp(roop.core.params.target_path, roop.core.params.output_path)
