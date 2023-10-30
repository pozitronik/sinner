from argparse import Namespace

from sinner.Parameters import Parameters
from sinner.gui.controls.FramePlayer.PygameFramePlayer import PygameFramePlayer
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.models.PerfCounter import PerfCounter
from tests.constants import state_frames_dir

parameters: Namespace = Parameters().parameters


def test_show_frame_wait() -> None:
    frames = DirectoryHandler(state_frames_dir, parameters)  # use DirectoryHandlers as an iterator
    player = PygameFramePlayer(100, 100, 'test')
    player.show()  # bootstrap pygame screen

    with PerfCounter() as timer:
        for index in frames:
            n_frame = frames.extract_frame(index)
            player.show_frame_wait(n_frame.frame, duration=0.5)
    assert int(timer.execution_time) == frames.fc / 2
    print(f"Execution time: {timer.execution_time}")
