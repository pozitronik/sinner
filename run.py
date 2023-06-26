#!/usr/bin/env python3
import signal
import sys

from roop.core import Core
from roop.parameters import Parameters
from roop.state import State
from roop.prototypes import get_video_handler, get_frame_processor
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
    core = Core(params=params, state=state, frames_handler=get_video_handler(params.target_path, params.frame_handler), frame_processor=get_frame_processor(params, state))

    core.run()
