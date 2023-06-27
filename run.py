#!/usr/bin/env python3
import signal
import sys

from roop.core import Core
from roop.handlers.frames.BaseFramesHandler import BaseFramesHandler
from roop.parameters import Parameters
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.utilities import limit_resources

if __name__ == '__main__':
    if sys.version_info < (3, 10):
        raise Exception('Python version is not supported - please upgrade to 3.10 or higher.')
    signal.signal(signal.SIGINT, lambda signal_number, frame: quit())

    params = Parameters()
    limit_resources(params.max_memory)
    frame_processors = BaseFrameProcessor.create(processors_name=params.frame_processors, parameters=params, state=state)
    frame_handler = BaseFramesHandler.create(handler_name=params.frame_handler, target_path=params.target_path)
    core = Core(params=params, frame_processors=frame_processors, frames_handler=frame_handler)
    core.run()
