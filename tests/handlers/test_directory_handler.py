import os
import shutil
from argparse import Namespace
from typing import Iterator

from numpy import ndarray
from sympy.testing import pytest

from sinner.Parameters import Parameters
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from tests.constants import TARGET_FC, FRAME_SHAPE, tmp_dir, state_frames_dir, target_mp4, result_mp4

parameters: Namespace = Parameters().parameters


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def setup_function():
    setup()


def get_test_object() -> DirectoryHandler:
    return DirectoryHandler(parameters=parameters, target_path=state_frames_dir)


def test_init() -> None:
    with pytest.raises(Exception):
        DirectoryHandler(parameters=parameters, target_path='not_existed_directory')
    with pytest.raises(Exception):
        DirectoryHandler(parameters=parameters, target_path=target_mp4)


def test_available() -> None:
    assert get_test_object().available() is True


def test_detect_fps() -> None:
    assert 1 == get_test_object().fps


def test_detect_fc() -> None:
    assert TARGET_FC == get_test_object().fc


def test_get_frames_paths() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir)
    assert TARGET_FC == len(frames_paths)
    first_item = frames_paths[0]
    assert (0, os.path.join(state_frames_dir, '00.png')) == first_item
    last_item = frames_paths.pop()
    assert (9, os.path.join(state_frames_dir, '09.png')) == last_item


def test_get_frames_paths_range() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(3, 8))
    assert 6 == len(frames_paths)
    first_item = frames_paths[0]
    assert first_item == (3, os.path.join(state_frames_dir, '03.png'))
    last_item = frames_paths.pop()
    assert (8, os.path.join(state_frames_dir, '08.png')) == last_item


def test_get_frames_paths_range_start() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(None, 8))
    assert 9 == len(frames_paths)
    first_item = frames_paths[0]
    assert (0, os.path.join(state_frames_dir, '00.png')) == first_item
    last_item = frames_paths.pop()
    assert (8, os.path.join(state_frames_dir, '08.png')) == last_item


def test_get_frames_paths_range_end() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(3, None))
    assert 7 == len(frames_paths)
    first_item = frames_paths[0]
    assert (3, os.path.join(state_frames_dir, '03.png')) == first_item
    last_item = frames_paths.pop()
    assert (9, os.path.join(state_frames_dir, '09.png')) == last_item


def test_get_frames_paths_range_empty() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(None, None))
    assert TARGET_FC == len(frames_paths)
    first_item = frames_paths[0]
    assert (0, os.path.join(state_frames_dir, '00.png')) == first_item
    last_item = frames_paths.pop()
    assert (9, os.path.join(state_frames_dir, '09.png')) == last_item


def test_get_frames_paths_range_fail() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(10, 1))
    assert 0 == len(frames_paths)


def test_extract_frame() -> None:
    first_frame = get_test_object().extract_frame(1)
    assert 1 == first_frame[0]
    assert isinstance(first_frame[1], ndarray)
    assert first_frame[1].shape == FRAME_SHAPE


def test_result() -> None:
    assert os.path.exists(result_mp4) is False
    assert get_test_object().result(from_dir=state_frames_dir, filename=result_mp4) is True


def tests_iterator() -> None:
    test_object = get_test_object()
    assert isinstance(test_object, Iterator)
    frame_counter = 0
    for frame_index in test_object:
        assert isinstance(frame_index, int)
        frame_counter += 1
    assert frame_counter == TARGET_FC

    test_object.current_frame_index = 8
    frame_counter = 0
    for frame_index in test_object:
        assert isinstance(frame_index, int)
        frame_counter += 1
    assert frame_counter == 2
