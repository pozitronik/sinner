from argparse import Namespace

from sinner.Parameters import Parameters
from sinner.gui.controls.FramePlayer.PygameFramePlayer import PygameFramePlayer
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.models.PerfCounter import PerfCounter
from sinner.utilities import compare_delta
from tests.constants import state_frames_dir

parameters: Namespace = Parameters().parameters


def test_show_frame_wait() -> None:
    frames = DirectoryHandler(state_frames_dir, parameters)  # use DirectoryHandlers as an iterator
    player = PygameFramePlayer(100, 100, 'test')
    player.show()  # bootstrap pygame screen

    f_time = 0.5

    while True:
        timer = None
        with PerfCounter() as timer:
            for index in frames:
                n_frame = frames.extract_frame(index)
                player.show_frame_wait(n_frame.frame, duration=f_time)
        if compare_delta(timer.execution_time, frames.fc * f_time, 0.1):
            print(f"Success on frame time: {f_time} sec, execution time: {timer.execution_time}, deviation: {(timer.execution_time % 1) / frames.fc} sec/frame")
            f_time /= 2
        else:
            print(f"Failed on frame time: {f_time} sec, execution time: {timer.execution_time}, deviation: {(timer.execution_time % 1) / frames.fc} sec/frame")
            break
