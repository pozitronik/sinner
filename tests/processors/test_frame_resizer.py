import pytest

from sinner.Parameters import Parameters
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.processors.frame.FrameResizer import FrameResizer
from sinner.typing import Frame
from sinner.validators.LoaderException import LoadingException
from tests.constants import target_png, tmp_dir


def test_resize_scale() -> None:
    assert (1080, 861) == CV2VideoHandler.read_image(target_png).shape[:2]
    test_object = FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}" --scale=0.3').parameters)
    processed_frame = test_object.process_frame(CV2VideoHandler.read_image(target_png))
    assert (processed_frame, Frame)
    assert (324, 258) == processed_frame.shape[:2]


def test_resize_scale_default() -> None:
    assert (1080, 861) == CV2VideoHandler.read_image(target_png).shape[:2]
    test_object = FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}"').parameters)
    processed_frame = test_object.process_frame(CV2VideoHandler.read_image(target_png))
    assert (processed_frame, Frame)
    assert (540, 430) == processed_frame.shape[:2]


def test_resize_scale_error() -> None:
    with pytest.raises(LoadingException):
        FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}" --scale=abd').parameters)


def test_resize_height() -> None:
    assert (1080, 861) == CV2VideoHandler.read_image(target_png).shape[:2]
    test_object = FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}" --height=800').parameters)
    processed_frame = test_object.process_frame(CV2VideoHandler.read_image(target_png))
    assert (processed_frame, Frame)
    assert (800, 637) == processed_frame.shape[:2]


def test_resize_height_error() -> None:
    with pytest.raises(LoadingException):
        FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}" --height=x800').parameters)


def test_resize_width() -> None:
    assert (1080, 861) == CV2VideoHandler.read_image(target_png).shape[:2]
    test_object = FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}" --width=1000').parameters)
    processed_frame = test_object.process_frame(CV2VideoHandler.read_image(target_png))
    assert (processed_frame, Frame)
    assert (1254, 1000) == processed_frame.shape[:2]


def test_resize_height_max() -> None:
    assert (1080, 861) == CV2VideoHandler.read_image(target_png).shape[:2]
    test_object = FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}" --height-max=500').parameters)
    processed_frame = test_object.process_frame(CV2VideoHandler.read_image(target_png))
    assert (processed_frame, Frame)
    assert (500, 398) == processed_frame.shape[:2]


def test_resize_height_min() -> None:
    assert (1080, 861) == CV2VideoHandler.read_image(target_png).shape[:2]
    test_object = FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}" --height-min=1200').parameters)
    processed_frame = test_object.process_frame(CV2VideoHandler.read_image(target_png))
    assert (processed_frame, Frame)
    assert (1200, 956) == processed_frame.shape[:2]


def test_resize_width_max() -> None:
    assert (1080, 861) == CV2VideoHandler.read_image(target_png).shape[:2]
    test_object = FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}" --width-max=300').parameters)
    processed_frame = test_object.process_frame(CV2VideoHandler.read_image(target_png))
    assert (processed_frame, Frame)
    assert (376, 300) == processed_frame.shape[:2]


def test_resize_width_min() -> None:
    assert (1080, 861) == CV2VideoHandler.read_image(target_png).shape[:2]
    test_object = FrameResizer(parameters=Parameters(f'--target-path="{target_png}" --output-path="{tmp_dir}" --width-min=1200').parameters)
    processed_frame = test_object.process_frame(CV2VideoHandler.read_image(target_png))
    assert (processed_frame, Frame)
    assert (1505, 1200) == processed_frame.shape[:2]
