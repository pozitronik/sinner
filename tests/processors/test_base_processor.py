import glob
import multiprocessing
import os.path
import shutil
from argparse import Namespace

import pytest

from sinner.Parameters import Parameters
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.processors.frame.DummyProcessor import DummyProcessor
from sinner.State import State
from sinner.typing import Frame
from sinner.utilities import read_image
from tests.constants import source_jpg, target_png, IMAGE_SHAPE, target_mp4, tmp_dir, TARGET_FC

parameters: Namespace = Parameters(f'--frame-processor=DummyProcessor --execution-provider=cpu --execution-threads={multiprocessing.cpu_count()} --source-path="{source_jpg}" --target-path="{target_mp4}" --output-path="{tmp_dir}"').parameters


def setup_function():
    setup()


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def get_test_handler() -> BaseFrameHandler:
    return VideoHandler(parameters=parameters, target_path=target_mp4)


def get_test_state() -> State:
    return State(
        parameters=parameters,
        frames_count=TARGET_FC,
        temp_dir=tmp_dir,
        processor_name='DummyProcessor',
        target_path=target_mp4
    )


def get_test_object() -> DummyProcessor:
    return DummyProcessor(parameters=parameters)


def test_create_factory():
    dummy_processor = BaseFrameProcessor.create('DummyProcessor', parameters=parameters)
    assert isinstance(dummy_processor, BaseFrameProcessor)
    with pytest.raises(Exception):
        BaseFrameProcessor.create('UnknownProcessor', parameters.parameters)


def test_init():
    test_object = get_test_object()
    assert (test_object, DummyProcessor)
    assert (test_object.max_memory, 12)


def test_process_frame():
    processed_frame = get_test_object().process_frame(read_image(target_png))
    assert (processed_frame, Frame)
    assert processed_frame.shape == IMAGE_SHAPE


def test_process():
    get_test_object().process(frames_handler=get_test_handler(), state=get_test_state())
    out_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/OUT/', '*.png')
    processed_files = glob.glob(out_dir)
    assert (len(processed_files), 98)


def test_process_frames_in_mem():
    out_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/OUT/')
    assert os.path.exists(out_dir) is False
    in_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/IN/')
    assert os.path.exists(in_dir) is False
    get_test_object().process_frames(get_test_handler(), get_test_state())  # in memory
    processed_files = glob.glob(os.path.join(out_dir, '*.png'))
    assert (len(processed_files),TARGET_FC)
    assert os.path.exists(in_dir) is False


def test_process_frames():
    out_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/OUT/')
    assert os.path.exists(out_dir) is False
    in_dir = os.path.join(tmp_dir, 'DummyProcessor/target.mp4/source.jpg/IN/')
    assert os.path.exists(in_dir) is False
    test_state: State = get_test_state()
    get_test_object().process_frames(get_test_handler().get_frames_paths(test_state.in_dir), test_state)  # via frames
    assert (len(glob.glob(os.path.join(in_dir, '*.png'))), TARGET_FC)
    assert (len(glob.glob(os.path.join(out_dir, '*.png'))), TARGET_FC)
