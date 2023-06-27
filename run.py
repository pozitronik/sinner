#!/usr/bin/env python3
import signal
import sys

from roop.core import Core
from roop.handlers.frames.BaseFramesHandler import BaseFramesHandler
from roop.parameters import Parameters
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.state import State
from roop.utilities import limit_resources


def destroy() -> None:
    # todo
    # if state.is_finished():
    #     clean_temp(params.target_path, params.keep_frames)
    exit()


if __name__ == '__main__':
    if sys.version_info < (3, 10):
        raise Exception('Python version is not supported - please upgrade to 3.10 or higher.')
    signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())

    params = Parameters()
    state = State(source_path=params.source_path, target_path=params.target_path, output_path=params.target_path, keep_frames=params.keep_frames)

    limit_resources(params.max_memory)
    frame_processor = BaseFrameProcessor.create(processors_name=params.frame_processors, parameters=params, state=state)
    frame_handler = BaseFramesHandler.create(handler_name=params.frame_handler, target_path=params.target_path)
    core = Core(params=params, state=state, frame_processor=frame_processor[0], frames_handler=frame_handler)

    core.run()
