import os
import shutil
from argparse import Namespace
from typing import Iterator

import pytest
from numpy import ndarray

from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.utilities import is_image
from tests.constants import IMAGE_SHAPE, tmp_dir, target_mp4, state_frames_dir, target_png, result_png


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def test_init() -> None:
    with pytest.raises(Exception):
        ImageHandler(target_path='not_existed_directory', parameters=Namespace())
    with pytest.raises(Exception):
        ImageHandler(target_path=target_mp4, parameters=Namespace())
    with pytest.raises(Exception):
        ImageHandler(target_path=state_frames_dir, parameters=Namespace())


def get_test_object() -> ImageHandler:
    return ImageHandler(target_path=target_png, parameters=Namespace())


def test_available() -> None:
    assert get_test_object().available() is True


def test_detect_fps() -> None:
    assert 1 == get_test_object().fps


def test_detect_fc() -> None:
    assert 1 == get_test_object().fc


def test_detect_resolution() -> None:
    assert (861, 1080) == get_test_object().resolution


def test_get_frames_paths() -> None:
    frames_paths = get_test_object().get_frames_paths(path=tmp_dir)
    assert 1 == len(frames_paths)
    first_item = frames_paths[0]
    assert (0, target_png) == first_item


def test_extract_frame() -> None:
    first_frame = get_test_object().extract_frame(1)
    assert 1 == first_frame.index
    assert isinstance(first_frame.frame, ndarray)
    assert first_frame.frame.shape == IMAGE_SHAPE


def test_result() -> None:
    assert os.path.exists(result_png) is False
    assert get_test_object().result(from_dir=os.path.dirname(target_png), filename=result_png) is True
    assert os.path.exists(result_png)
    assert is_image(result_png)


def tests_iterator() -> None:
    test_object = get_test_object()
    assert isinstance(test_object, Iterator)
    frame_counter = 0
    for frame_index in test_object:
        assert isinstance(frame_index, int)
        frame_counter += 1
    assert frame_counter == 1
