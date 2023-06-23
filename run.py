#!/usr/bin/env python3
import platform
import signal
import sys

import tensorflow

from roop.core import Core
from roop.handlers.video import BaseVideoHandler
from roop.handlers.video.CV2VideoHandler import CV2VideoHandler
from roop.handlers.video.FFmpegVideoHandler import FFmpegVideoHandler
from roop.parameters import Parameters
from roop.processors.frame import BaseFrameProcessor
from roop.processors.frame.FaceSwapper import FaceSwapper
from roop.state import State


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


def destroy() -> None:
    # todo
    # if state.is_finished():
    #     clean_temp(params.target_path, params.keep_frames)
    exit()


def get_video_handler(target_path: str, handler_name: str = 'ffmpeg') -> BaseVideoHandler:  # temporary, will be replaced with a factory
    if 'cv2' == handler_name: return CV2VideoHandler(target_path)
    return FFmpegVideoHandler(target_path)


def get_frame_processor(state: State) -> BaseFrameProcessor:  # temporary, will be replaced with a factory
    return FaceSwapper(params, state)


if __name__ == '__main__':
    if sys.version_info < (3, 9):
        raise Exception('Python version is not supported - please upgrade to 3.9 or higher.')
    signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())
    limit_resources()

    params = Parameters()
    state = State(params)
    state.create()

    core = Core(params=params, state=state, video_handler=get_video_handler(params.target_path, params.video_handler), frame_processor=get_frame_processor(state))

    core.run()
