import multiprocessing

from sinner.processors.frame.FaceSwapper import FaceSwapper
from sinner.state import State
from sinner.utilities import TEMP_DIRECTORY, resolve_relative_path
from tests.constants import source_jpg, target_png


def get_test_state() -> State:
    return State(
        source_path=source_jpg,
        target_path=target_png,
        frames_count=1,
        temp_dir=resolve_relative_path(TEMP_DIRECTORY)
    )


def test_init():
    test_object = FaceSwapper(execution_providers=['CPUExecutionProvider'], execution_threads=multiprocessing.cpu_count(), max_memory=12, many_faces=False, source_path=source_jpg, state=get_test_state())
    assert (test_object, FaceSwapper)


def test_process_frame():
    pass


def test_swap_face():
    pass
