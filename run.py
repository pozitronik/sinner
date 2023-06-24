#!/usr/bin/env python3
import signal
import sys


from roop.core import Core
from roop.handlers.video.BaseVideoHandler import BaseVideoHandler
from roop.handlers.video.CV2VideoHandler import CV2VideoHandler
from roop.handlers.video.FFmpegVideoHandler import FFmpegVideoHandler
from roop.parameters import Parameters
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.processors.frame.FaceSwapper import FaceSwapper
from roop.state import State
from roop.utilities import limit_resources


def destroy() -> None:
    # todo
    # if state.is_finished():
    #     clean_temp(params.target_path, params.keep_frames)
    exit()


def get_video_handler(target_path: str, handler_name: str = 'ffmpeg') -> BaseVideoHandler:  # temporary, will be replaced with a factory
    if 'cv2' == handler_name:
        return CV2VideoHandler(target_path)
    return FFmpegVideoHandler(target_path)


def get_frame_processor(state_var: State) -> BaseFrameProcessor:  # temporary, will be replaced with a factory
    return FaceSwapper(params, state_var)


if __name__ == '__main__':
    if sys.version_info < (3, 10):
        raise Exception('Python version is not supported - please upgrade to 3.10 or higher.')
    signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())

    params = Parameters()
    state = State(params)
    state.create()
    limit_resources(params.max_memory)
    core = Core(params=params, state=state, video_handler=get_video_handler(params.target_path, params.video_handler), frame_processor=get_frame_processor(state))

    core.run()
