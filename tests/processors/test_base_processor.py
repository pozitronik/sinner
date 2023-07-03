import multiprocessing

from sinner.processors.frame.DummyProcessor import DummyProcessor
from sinner.state import State
from sinner.typing import Frame
from sinner.utilities import TEMP_DIRECTORY, resolve_relative_path, read_image
from tests.constants import source_jpg, target_png, IMAGE_SHAPE


def get_test_state() -> State:
    return State(
        source_path=source_jpg,
        target_path=target_png,
        frames_count=1,
        temp_dir=resolve_relative_path(TEMP_DIRECTORY)
    )


def get_test_object() -> DummyProcessor:
    return DummyProcessor(execution_providers=['CPUExecutionProvider'], execution_threads=multiprocessing.cpu_count(), max_memory=12, state=get_test_state())


def test_create_factory():
    pass


def test_init():
    test_object = get_test_object()
    assert (test_object, DummyProcessor)


def test_process_frame():
    processed_frame = get_test_object().process_frame(read_image(target_png))
    assert (processed_frame, Frame)
    assert processed_frame.shape == IMAGE_SHAPE


def test_process():
    pass


def test_process_frames():
    pass


def test_multi_process_frame():
    pass
