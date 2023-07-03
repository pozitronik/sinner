import multiprocessing

from sinner.face_analyser import FaceAnalyser
from sinner.processors.frame.FaceSwapper import FaceSwapper
from sinner.state import State
from sinner.typing import Frame, FaceSwapperType
from sinner.utilities import TEMP_DIRECTORY, resolve_relative_path, read_image
from tests.constants import source_jpg, target_png


def get_test_state() -> State:
    return State(
        source_path=source_jpg,
        target_path=target_png,
        frames_count=1,
        temp_dir=resolve_relative_path(TEMP_DIRECTORY)
    )


def get_test_object() -> FaceSwapper:
    return FaceSwapper(execution_providers=['CPUExecutionProvider'], execution_threads=multiprocessing.cpu_count(), max_memory=12, many_faces=False, source_path=source_jpg, state=get_test_state())


def test_init():
    test_object = get_test_object()
    assert (test_object, FaceSwapper)
    assert (test_object._face_analyser, FaceAnalyser)
    assert (test_object._face_swapper, FaceSwapperType)


def test_process_frame():
    processed_frame = get_test_object().process_frame(read_image(target_png))
    assert (processed_frame, Frame)
