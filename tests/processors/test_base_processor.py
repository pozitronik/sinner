import multiprocessing

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.processors.frame.DummyProcessor import DummyProcessor
from sinner.state import State
from sinner.typing import Frame
from sinner.utilities import read_image
from tests.constants import source_jpg, target_png, IMAGE_SHAPE, target_mp4, tmp_dir


def get_test_handler() -> BaseFrameHandler:
    return VideoHandler(target_path=target_mp4)


def get_test_state() -> State:
    return State(
        source_path=source_jpg,
        target_path=target_mp4,
        frames_count=98,
        temp_dir=tmp_dir
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
    get_test_object().process(frames_handler=get_test_handler())


def test_process_frames():
    get_test_object().process_frames(get_test_handler())  # in memory
    get_test_object().process_frames(get_test_handler().get_frames_paths(get_test_state().in_dir))  # via frames


def test_multi_process_frame():
    pass
