import os
import shutil
from argparse import Namespace
from typing import Iterator

import pytest
from numpy import ndarray

from sinner.handlers.frame.FFmpegVideoHandler import FFmpegVideoHandler
from sinner.utilities import resolve_relative_path
from tests.constants import TARGET_FPS, TARGET_FC, FRAME_SHAPE, tmp_dir, target_mp4, result_mp4, state_frames_dir, TARGET_RESOLUTION, broken_mp4, BROKEN_FC


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def setup_function():
    setup()


def get_test_object() -> FFmpegVideoHandler:
    return FFmpegVideoHandler(target_path=target_mp4, parameters=Namespace())


def get_broken_object() -> FFmpegVideoHandler:
    return FFmpegVideoHandler(parameters=Namespace(), target_path=broken_mp4)


def test_available() -> None:
    assert get_test_object().available() is True


def test_detect_fps() -> None:
    assert TARGET_FPS == get_test_object().fps


def test_detect_fc() -> None:
    assert TARGET_FC == get_test_object().fc


def test_detect_broken_fc() -> None:
    assert BROKEN_FC == get_broken_object().fc


def test_detect_resolution() -> None:
    assert TARGET_RESOLUTION == get_test_object().resolution


def test_get_frames_paths() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir)
    assert TARGET_FC == len(frames_paths)
    first_item = frames_paths[0]
    assert (0, resolve_relative_path(os.path.join(tmp_dir, '00.png'))) == first_item
    last_item = frames_paths.pop()
    assert (9, resolve_relative_path(os.path.join(tmp_dir, '09.png'))) == last_item


def test_get_frames_paths_range() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(3, 8))
    assert 6 == len(frames_paths)
    first_item = frames_paths[0]
    assert first_item == (3, resolve_relative_path(os.path.join(tmp_dir, '03.png')))
    last_item = frames_paths.pop()
    assert (8, resolve_relative_path(os.path.join(tmp_dir, '08.png'))) == last_item


def test_get_frames_paths_range_start() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(None, 8))
    assert 9 == len(frames_paths)
    first_item = frames_paths[0]
    assert (0, resolve_relative_path(os.path.join(tmp_dir, '00.png'))) == first_item
    last_item = frames_paths.pop()
    assert (8, resolve_relative_path(os.path.join(tmp_dir, '08.png'))) == last_item


def test_get_frames_paths_range_end() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(3, None))
    assert 7 == len(frames_paths)
    first_item = frames_paths[0]
    assert (3, resolve_relative_path(os.path.join(tmp_dir, '03.png'))) == first_item
    last_item = frames_paths.pop()
    assert (9, resolve_relative_path(os.path.join(tmp_dir, '09.png'))) == last_item


def test_get_frames_paths_range_empty() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(None, None))
    assert TARGET_FC == len(frames_paths)
    first_item = frames_paths[0]
    assert (0, resolve_relative_path(os.path.join(tmp_dir, '00.png'))) == first_item
    last_item = frames_paths.pop()
    assert (9, resolve_relative_path(os.path.join(tmp_dir, '09.png'))) == last_item


def test_get_frames_paths_range_fail() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir, frames_range=(10, 1))
    assert 0 == len(frames_paths)


def test_extract_frame() -> None:
    first_frame = get_test_object().extract_frame(1)
    assert 1 == first_frame.index
    assert isinstance(first_frame.frame, ndarray)
    assert first_frame.frame.shape == FRAME_SHAPE


def test_result() -> None:
    if 'CI' in os.environ:
        pytest.skip("This test is not ready for GitHub CI")
    assert os.path.exists(result_mp4) is False
    assert get_test_object().result(from_dir=state_frames_dir, filename=result_mp4) is True
    assert os.path.exists(result_mp4)
    target = FFmpegVideoHandler(target_path=result_mp4, parameters=Namespace())
    assert target.fc == TARGET_FC
    assert target.fps == TARGET_FPS


def tests_iterator() -> None:
    cv2 = get_test_object()
    assert isinstance(cv2, Iterator)
    frame_counter = 0
    for frame_index in cv2:
        assert isinstance(frame_index, int)
        frame_counter += 1
    assert frame_counter == TARGET_FC

    cv2.current_frame_index = 8
    frame_counter = 0
    for frame_index in cv2:
        assert isinstance(frame_index, int)
        frame_counter += 1
    assert frame_counter == 2
