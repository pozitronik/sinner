import multiprocessing

from gfpgan import GFPGANer  # type: ignore[attr-defined]

from sinner.face_analyser import FaceAnalyser
from sinner.processors.frame.FaceEnhancer import FaceEnhancer
from sinner.state import State
from sinner.typing import Frame
from sinner.utilities import read_image
from tests.constants import source_jpg, target_png, IMAGE_SHAPE, tmp_dir


def get_test_state() -> State:
    return State(
        source_path=source_jpg,
        target_path=target_png,
        frames_count=1,
        temp_dir=tmp_dir
    )


def get_test_object() -> FaceEnhancer:
    return FaceEnhancer(execution_providers=['CPUExecutionProvider'], execution_threads=multiprocessing.cpu_count(), max_memory=12, state=get_test_state())


def test_init():
    test_object = get_test_object()
    assert (test_object, FaceEnhancer)
    assert (test_object._face_analyser, FaceAnalyser)
    assert (test_object._face_enhancer, GFPGANer)


def test_process_frame():
    processed_frame = get_test_object().process_frame(read_image(target_png))
    assert (processed_frame, Frame)
    assert processed_frame.shape == IMAGE_SHAPE
