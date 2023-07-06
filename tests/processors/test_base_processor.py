import glob
import multiprocessing
import os.path
import shutil
from argparse import Namespace

import pytest

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.parameters import Parameters
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.processors.frame.DummyProcessor import DummyProcessor
from sinner.state import State
from sinner.typing import Frame
from sinner.utilities import read_image
from tests.constants import source_jpg, target_png, IMAGE_SHAPE, target_mp4, tmp_dir


def setup_function(function):
    setup()


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


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


def get_test_namespace() -> Namespace:
    return Namespace(
        frame_processor=['DummyProcessor'],
        execution_provider=['CPUExecutionProvider'],
        execution_threads=multiprocessing.cpu_count(),
        max_memory=12,
        source_path=source_jpg,
        target_path=target_mp4,
        output_path=tmp_dir,
        fps=None,
        keep_audio=False,
        keep_frames=False,
        many_faces=False,
        extract_frames=False,
        frame_handler=None,
        temp_dir=tmp_dir,
        benchmark=None
    )


def test_create_factory():
    parameters: Parameters = Parameters(get_test_namespace())
    dummy_processor = BaseFrameProcessor.create('DummyProcessor', parameters=parameters, state=get_test_state())
    assert isinstance(dummy_processor, BaseFrameProcessor)
    assert dummy_processor.state.frames_count == 98
    assert dummy_processor.max_memory == 12
    with pytest.raises(Exception):
        BaseFrameProcessor.create('UnknownProcessor', parameters, state=get_test_state())


def test_init():
    test_object = get_test_object()
    assert (test_object, DummyProcessor)
    assert (test_object.max_memory, 12)


def test_process_frame():
    processed_frame = get_test_object().process_frame(read_image(target_png))
    assert (processed_frame, Frame)
    assert processed_frame.shape == IMAGE_SHAPE


def test_process():
    get_test_object().process(frames_handler=get_test_handler())
    out_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/OUT/', '*.png')
    processed_files = glob.glob(out_dir)
    assert (len(processed_files), 98)


def test_process_frames_in_mem():
    out_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/OUT/')
    assert os.path.exists(out_dir) is False
    in_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/IN/')
    assert os.path.exists(in_dir) is False
    get_test_object().process_frames(get_test_handler())  # in memory
    processed_files = glob.glob(os.path.join(out_dir, '*.png'))
    assert (len(processed_files), 98)
    assert os.path.exists(in_dir) is False


def test_process_frames():
    out_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/OUT/')
    assert os.path.exists(out_dir) is False
    in_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/IN/')
    assert os.path.exists(in_dir) is False
    get_test_object().process_frames(get_test_handler().get_frames_paths(get_test_state().in_dir))  # via frames
    assert (len(glob.glob(os.path.join(in_dir, '*.png'))), 98)
    assert (len(glob.glob(os.path.join(out_dir, '*.png'))), 98)
