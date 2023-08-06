import os.path
import shutil
from argparse import Namespace
from typing import List

import pytest

from sinner.Parameters import Parameters
from sinner.State import State
from tests.constants import tmp_dir, target_mp4, source_jpg, target_png, TARGET_FC, state_frames_dir

parameters: Namespace = Parameters(f'--frame-processor=DummyProcessor --source-path="{source_jpg}" --target-path="{target_mp4}" --output-path="{tmp_dir}"').parameters


def copy_files(from_dir: str, to_dir: str, filenames: List[str]) -> None:
    for file_name in filenames:
        source_path = os.path.join(from_dir, file_name)
        destination_path = os.path.join(to_dir, file_name)

        if os.path.isfile(source_path):
            shutil.copy2(source_path, destination_path)


def setup_function():
    setup()


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def test_raise_on_relative_path() -> None:
    with pytest.raises(Exception):
        State(parameters=Namespace(), target_path=None, temp_dir='data/temp', frames_count=0, processor_name='')


def test_basic() -> None:
    state = State(parameters=Namespace(), target_path=None, temp_dir=tmp_dir, frames_count=0, processor_name='')
    assert os.path.exists(tmp_dir) is False
    assert state.source_path is None
    assert state.target_path is None
    assert state._temp_dir == tmp_dir  # absolute path used
    assert state.path == os.path.normpath(tmp_dir)

    assert os.path.exists(os.path.normpath(tmp_dir)) is True

    assert state.is_started is False
    assert state.is_finished is False

    assert state.processed_frames_count == 0
    assert state.zfill_length == 1
    assert state.get_frame_processed_name(100) == os.path.abspath(os.path.join(tmp_dir, '100.png'))


def test_state_names_generation() -> None:
    state = State(parameters=Namespace(), target_path=target_mp4, temp_dir=tmp_dir, frames_count=0, processor_name='DummyProcessor')
    assert os.path.exists(os.path.join(tmp_dir, 'DummyProcessor/target.mp4')) is False
    assert state.source_path is None
    assert state.target_path == target_mp4
    assert state._temp_dir == tmp_dir  # absolute path used
    assert state.path == os.path.abspath(os.path.join(tmp_dir, 'DummyProcessor/target.mp4'))

    assert os.path.exists(os.path.join(tmp_dir, 'DummyProcessor/target.mp4')) is True

    state = State(parameters=Namespace(source=source_jpg), target_path=target_png, temp_dir=tmp_dir, frames_count=0, processor_name='DummyProcessor')
    assert os.path.exists(os.path.join(tmp_dir, 'DummyProcessor/target.png/source.jpgT')) is False
    assert state.source_path == source_jpg
    assert state.target_path == target_png
    assert state._temp_dir == tmp_dir  # absolute path used
    assert state.path == os.path.abspath(os.path.join(tmp_dir, 'DummyProcessor/target.png/source.jpg'))
    assert os.path.exists(os.path.join(tmp_dir, 'DummyProcessor/target.png/source.jpg')) is True


def test_states() -> None:
    state = State(parameters=Namespace(), target_path=target_mp4, temp_dir=tmp_dir, frames_count=TARGET_FC, processor_name='DummyProcessor')
    assert state.zfill_length == 2
    assert state.is_started is False
    assert state.is_finished is False
    assert state.processed_frames_count == 0
    assert state.unprocessed_frames_count == 10

    copy_files(state_frames_dir, state.path, ['00.png'])
    assert state.is_started is True
    assert state.is_finished is False
    assert state.processed_frames_count == 1
    assert state.unprocessed_frames_count == 9

    copy_files(state_frames_dir, state.path, ['01.png', '02.png', '03.png', '04.png'])
    assert state.is_started is True
    assert state.is_finished is False
    assert state.processed_frames_count == 5
    assert state.unprocessed_frames_count == 5

    copy_files(state_frames_dir, state.path, ['05.png', '06.png', '07.png', '08.png', '09.png'])
    assert state.is_started is False
    assert state.is_finished is True
    assert state.processed_frames_count == 10
    assert state.unprocessed_frames_count == 0


def test_final_check_ok():
    state = State(parameters=Namespace(), target_path=target_mp4, temp_dir=tmp_dir, frames_count=TARGET_FC, processor_name='DummyProcessor')
    shutil.copytree(state_frames_dir, state.path, dirs_exist_ok=True)
    assert state.final_check() is True


def test_final_check_fail_state():
    state = State(parameters=Namespace(), target_path=target_mp4, temp_dir=tmp_dir, frames_count=TARGET_FC, processor_name='DummyProcessor')
    shutil.copytree(state_frames_dir, state.path, dirs_exist_ok=True)
    os.remove(os.path.join(state.path, '05.png'))
    assert state.final_check() is False


def test_final_check_fail_zero_files():
    state = State(parameters=Namespace(), target_path=target_mp4, temp_dir=tmp_dir, frames_count=TARGET_FC, processor_name='DummyProcessor')
    shutil.copytree(state_frames_dir, state.path, dirs_exist_ok=True)
    with open(os.path.join(state.path, '04.png'), 'r+') as file:
        file.truncate(0)
    assert state.final_check() is False
