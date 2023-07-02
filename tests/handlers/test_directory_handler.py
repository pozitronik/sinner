import os
import shutil
from typing import Iterator

from numpy import ndarray
from sympy.testing import pytest

from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from tests.constants import TARGET_FC, FRAME_SHAPE, tmp_dir, state_frames_dir, target_mp4, result_mp4


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def get_test_object() -> DirectoryHandler:
    return DirectoryHandler(target_path=state_frames_dir)


def test_init() -> None:
    with pytest.raises(Exception):
        DirectoryHandler(target_path='not_existed_directory')
    with pytest.raises(Exception):
        DirectoryHandler(target_path=target_mp4)


def test_available() -> None:
    assert get_test_object().available() is True


def test_detect_fps() -> None:
    assert 1 == get_test_object().detect_fps()


def test_detect_fc() -> None:
    assert TARGET_FC == get_test_object().detect_fc()


def test_get_frames_paths() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir)
    assert TARGET_FC == len(frames_paths)
    first_item = frames_paths[0]
    assert (1, os.path.join(state_frames_dir, '01.png')) == first_item
    last_item = frames_paths.pop()
    assert (TARGET_FC, os.path.join(state_frames_dir, '98.png')) == last_item


def test_extract_frame() -> None:
    first_frame = get_test_object().extract_frame(1)
    assert 1 == first_frame[0]
    assert isinstance(first_frame[1], ndarray)
    assert first_frame[1].shape == FRAME_SHAPE


def test_result() -> None:
    assert os.path.exists(result_mp4) is False
    assert get_test_object().result(from_dir=state_frames_dir, filename=result_mp4) is False


def tests_iterator() -> None:
    test_object = get_test_object()
    assert isinstance(test_object, Iterator)
    frame_counter = 0
    for frame_index in test_object:
        assert isinstance(frame_index, int)
        frame_counter += 1
    assert frame_counter == TARGET_FC

    test_object.current_frame_index = 90
    frame_counter = 0
    for frame_index in test_object:
        assert isinstance(frame_index, int)
        frame_counter += 1
    assert frame_counter == 8
