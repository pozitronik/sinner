import os.path
import shutil

from sinner.helpers import FrameHelper
from tests.constants import target_png, tmp_dir


def setup_function():
    setup()


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def test_create() -> None:
    default_test_frame = FrameHelper.create()
    assert default_test_frame.shape == (1, 1, 3)

    test_frame = FrameHelper.create((10, 15))
    assert test_frame.shape == (10, 15, 3)


def test_read_from_image() -> None:
    image = FrameHelper.read_from_image(target_png)
    assert (1080, 861, 3) == image.shape
    assert 2789640 == image.size


def test_save_to_image() -> None:
    file_path = os.path.join(tmp_dir, 'save.png')
    assert not os.path.exists(file_path)
    image = FrameHelper.create((10, 15))
    assert FrameHelper.write_to_image(image, file_path) is True
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) == 97


def test_save_to_image_copy() -> None:
    file_path = os.path.join(tmp_dir, os.path.basename(target_png))
    print(file_path)  # for CI
    assert not os.path.exists(file_path)
    image = FrameHelper.read_from_image(target_png)
    assert 2789640 == image.size
    assert FrameHelper.write_to_image(image, file_path) is True
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) == 1499926


def test_scale() -> None:
    test_frame = FrameHelper.create((10, 15))
    resized_frame = FrameHelper.scale(test_frame, 10)
    assert resized_frame.shape == (100, 150, 3)

    resized_frame = FrameHelper.scale(test_frame, 0.3)
    assert resized_frame.shape == (3, 4, 3)

    resized_frame = FrameHelper.scale(test_frame, 1 / 3)
    assert resized_frame.shape == (3, 5, 3)


def test_scale_image() -> None:
    image = FrameHelper.read_from_image(target_png)
    assert (1080, 861, 3) == image.shape
    resized_frame = FrameHelper.scale(image, 10)
    assert resized_frame.shape == (10800, 8610, 3)

    resized_frame = FrameHelper.scale(image, 0.3)
    assert resized_frame.shape == (324, 258, 3)

    resized_frame = FrameHelper.scale(image, 1 / 3)
    assert resized_frame.shape == (360, 287, 3)


def test_resize_proportional() -> None:
    test_frame = FrameHelper.create((10, 15))

    # zoom the frame:

    # proportions are equal to both sizes
    resized_frame = FrameHelper.resize_proportionally(test_frame, (20, 30))
    assert resized_frame.shape == (20, 30, 3)
    # new proportions bounds are not equal (height is bigger)
    resized_frame = FrameHelper.resize_proportionally(test_frame, (30, 30))
    assert resized_frame.shape == (20, 30, 3)
    # new proportions bounds are not equal (width is bigger)
    resized_frame = FrameHelper.resize_proportionally(test_frame, (20, 50))
    assert resized_frame.shape == (20, 30, 3)

    # shrunk the frame:

    # proportions are equal to both sizes
    resized_frame = FrameHelper.resize_proportionally(test_frame, (3, 5))
    assert resized_frame.shape == (3, 4, 3)
    # new proportions bounds are not equal (height is bigger)
    resized_frame = FrameHelper.resize_proportionally(test_frame, (5, 5))
    assert resized_frame.shape == (3, 5, 3)
    # new proportions bounds are not equal (width is bigger)
    resized_frame = FrameHelper.resize_proportionally(test_frame, (3, 3))
    assert resized_frame.shape == (2, 3, 3)

    # new proportions bounds are not equal (width is bigger)
    resized_frame = FrameHelper.resize_proportionally(test_frame, (1, 1))
    assert resized_frame.shape == (1, 1, 3)


def test_resize_proportional_image() -> None:
    test_image = FrameHelper.read_from_image(target_png)
    assert (1080, 861, 3) == test_image.shape
    # zoom the frame:

    # proportions are equal to both sizes
    resized_image = FrameHelper.resize_proportionally(test_image, (2000, 3000))
    assert resized_image.shape == (2000, 1594, 3)
    # new proportions bounds are not equal (height is bigger)
    resized_image = FrameHelper.resize_proportionally(test_image, (3000, 3000))
    assert resized_image.shape == (3000, 2391, 3)
    # new proportions bounds are not equal (width is bigger)
    resized_image = FrameHelper.resize_proportionally(test_image, (2000, 5000))
    assert resized_image.shape == (2000, 1594, 3)

    # shrunk the image:

    # proportions are equal to both sizes
    resized_image = FrameHelper.resize_proportionally(test_image, (300, 500))
    assert resized_image.shape == (300, 239, 3)
    # new proportions bounds are not equal (height is bigger)
    resized_image = FrameHelper.resize_proportionally(test_image, (500, 500))
    assert resized_image.shape == (500, 398, 3)
    # new proportions bounds are not equal (width is bigger)
    resized_image = FrameHelper.resize_proportionally(test_image, (300, 300))
    assert resized_image.shape == (300, 239, 3)

    # new proportions bounds are not equal (width is bigger)
    resized_image = FrameHelper.resize_proportionally(test_image, (1, 1))
    assert resized_image.shape == (1, 1, 3)
