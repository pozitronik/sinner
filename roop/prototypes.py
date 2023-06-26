from roop.handlers.frames.BaseFramesHandler import BaseFramesHandler
from roop.handlers.frames.CV2VideoHandler import CV2VideoHandler
from roop.handlers.frames.FFmpegVideoHandler import FFmpegVideoHandler
from roop.parameters import Parameters
from roop.processors.frame import BaseFrameProcessor
from roop.processors.frame.FaceSwapper import FaceSwapper
from roop.state import State


def get_video_handler(target_path: str, handler_name: str = 'ffmpeg') -> BaseFramesHandler:  # temporary, will be replaced with a factory
    if 'cv2' == handler_name:
        return CV2VideoHandler(target_path)
    return FFmpegVideoHandler(target_path)


def get_frame_processor(params: Parameters, state_var: State) -> BaseFrameProcessor:  # temporary, will be replaced with a factory
    return FaceSwapper(params, state_var)
