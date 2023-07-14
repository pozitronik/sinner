import os
import shutil
from typing import Iterator

import pytest
from numpy import ndarray

from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.utilities import resolve_relative_path
from tests.constants import TARGET_FPS, TARGET_FC, FRAME_SHAPE

target_mp4: str = resolve_relative_path('../data/targets/target.mp4', __file__)
tmp_dir: str = resolve_relative_path('../data/temp', __file__)
state_frames_dir: str = resolve_relative_path('../data/frames', __file__)
result_mp4: str = os.path.join(tmp_dir, 'result.mp4')


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def get_test_object() -> VideoHandler:
    return VideoHandler(target_path=target_mp4)


def test_available() -> None:
    assert get_test_object().available() is True


def test_detect_fps() -> None:
    assert TARGET_FPS == get_test_object().detect_fps()


def test_detect_fc() -> None:
    assert TARGET_FC == get_test_object().detect_fc()


def test_get_frames_paths() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir)
    assert TARGET_FC == len(frames_paths)
    first_item = frames_paths[0]
    assert (1, resolve_relative_path('../data/temp/01.png')) == first_item
    last_item = frames_paths.pop()
    assert (TARGET_FC, resolve_relative_path('../data/temp/10.png')) == last_item


def test_extract_frame() -> None:
    first_frame = get_test_object().extract_frame(1)
    assert 1 == first_frame[0]
    assert isinstance(first_frame[1], ndarray)
    assert first_frame[1].shape == FRAME_SHAPE


@pytest.mark.skip(reason="This test is not ready for GitHub CI")
def test_result() -> None:
    assert os.path.exists(result_mp4) is False
    assert get_test_object().result(from_dir=state_frames_dir, filename=result_mp4) is True
    assert os.path.exists(result_mp4)
    target = VideoHandler(target_path=result_mp4)
    assert target.fc == TARGET_FC
    assert target.fps == TARGET_FPS


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
