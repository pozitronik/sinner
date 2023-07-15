import os.path
import shutil
from argparse import Namespace

from sinner.Parameters import Parameters
from sinner.State import State
from tests.constants import tmp_dir, target_mp4, source_jpg, target_png

parameters: Namespace = Parameters(f'--frame-processor=DummyProcessor --source-path="{source_jpg}" --target-path="{target_mp4}" --output-path="{tmp_dir}"').parameters


def setup_function():
    setup()


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def test_basic() -> None:
    state = State(parameters=Namespace(), target_path=None, temp_dir='data/temp', frames_count=0, processor_name='')

    assert os.path.exists('data/temp/IN') is False
    assert os.path.exists('data/temp/OUT') is False
    assert state.source_path is None
    assert state.target_path is None
    assert state._temp_dir == os.path.abspath(os.path.normpath('data/temp'))  # relative path used
    assert state.in_dir == os.path.abspath(os.path.normpath('data/temp/IN'))
    assert state.out_dir == os.path.abspath(os.path.normpath('data/temp/OUT'))

    assert os.path.exists('data/temp/IN') is True
    assert os.path.exists('data/temp/OUT') is True

    assert state.is_started is False
    assert state.is_finished is False

    assert state.processed_frames_count == 0
    assert state.zfill_length == 1
    assert state.get_frame_processed_name(100) == os.path.abspath(os.path.normpath('data/temp/OUT/100.png'))


def test_state_names_generation_absolute_path() -> None:
    state = State(parameters=Namespace(), target_path=None, temp_dir=tmp_dir, frames_count=0, processor_name='')
    assert os.path.exists('data/temp/IN') is False
    assert os.path.exists('data/temp/OUT') is False
    assert state.source_path is None
    assert state.target_path is None
    assert state._temp_dir == tmp_dir  # absolute path used
    assert state.in_dir == os.path.abspath(os.path.abspath('data/temp/IN'))
    assert state.out_dir == os.path.abspath(os.path.abspath('data/temp/OUT'))

    assert os.path.exists('data/temp/IN') is True
    assert os.path.exists('data/temp/OUT') is True


def test_state_names_generation() -> None:
    state = State(parameters=Namespace(), target_path=target_mp4, temp_dir=tmp_dir, frames_count=0, processor_name='DummyProcessor')
    assert os.path.exists('data/temp/DummyProcessor/target.mp4/IN') is False
    assert os.path.exists('data/temp/DummyProcessor/target.mp4/OUT') is False
    assert state.source_path is None
    assert state.target_path == target_mp4
    assert state._temp_dir == tmp_dir  # absolute path used
    assert state.in_dir == os.path.abspath(os.path.normpath('data/temp/DummyProcessor/target.mp4/IN'))
    assert state.out_dir == os.path.abspath(os.path.normpath('data/temp/DummyProcessor/target.mp4/OUT'))

    assert os.path.exists('data/temp/DummyProcessor/target.mp4/IN') is True
    assert os.path.exists('data/temp/DummyProcessor/target.mp4/OUT') is True

    state = State(parameters=Namespace(source=source_jpg), target_path=target_png, temp_dir=tmp_dir, frames_count=0, processor_name='DummyProcessor')
    assert os.path.exists('data/temp/DummyProcessor/target.png/source.jpg/IN') is False
    assert os.path.exists('data/temp/DummyProcessor/target.png/source.jpg/OUT') is False
    assert state.source_path == source_jpg
    assert state.target_path == target_png
    assert state._temp_dir == tmp_dir  # absolute path used
    assert state.in_dir == os.path.abspath(os.path.normpath('data/temp/DummyProcessor/target.png/source.jpg/IN'))
    assert state.out_dir == os.path.abspath(os.path.normpath('data/temp/DummyProcessor/target.png/source.jpg/OUT'))

    assert os.path.exists('data/temp/DummyProcessor/target.png/source.jpg/IN') is True
    assert os.path.exists('data/temp/DummyProcessor/target.png/source.jpg/OUT') is True
