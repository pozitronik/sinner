# helper methods to work with frames entity
import os.path
from pathlib import Path

import cv2
from numpy import fromfile, uint8, full, dstack
from psutil import WINDOWS

from sinner.typing import Frame

EmptyFrame = full([1, 1, 3], 255, dtype=uint8)


# be noticed that frames shapes have HEIGHT, WIDTH order, so all methods here use that order too
def create(size: tuple[int, int] = (1, 1)) -> Frame:
    return full([*size, 3], 255, dtype=uint8)


def read_from_image(path: str) -> Frame:
    if WINDOWS:  # issue #511
        image = cv2.imdecode(fromfile(path, dtype=uint8), cv2.IMREAD_UNCHANGED)
        if len(image.shape) == 2:  # fixes the b/w images issue
            image = dstack([image] * 3)
        if image.shape[2] == 4:  # fixes the alpha-channel issue
            image = image[:, :, :3]
        return image
    else:
        return cv2.imread(path)


def write_to_image(image: Frame, path: str) -> bool:
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)  # todo: can be replaced with os.makedirs
    if WINDOWS:  # issue #511
        is_success, im_buf_arr = cv2.imencode(".png", image)
        im_buf_arr.tofile(path)
        return is_success
    else:
        return cv2.imwrite(path, image)


def scale(frame: Frame, scale_: float = 0.2) -> Frame:
    if 1 == scale_:
        return frame
    current_height, current_width = frame.shape[:2]
    # note: cv2.resize uses WIDTH, HEIGHT order, instead of frames HEIGHT, WIDTH order
    return cv2.resize(frame, (int(current_width * scale_), int(current_height * scale_)))


def resize_proportionally(frame: Frame, new_shape: tuple[int, int]) -> Frame:
    """
    Proportionally resizes frame to the requested shape
    :param frame: the initial frame
    :param new_shape: tuple[HEIGHT, WIDTH] new shape bounds
    :return: resized shape
    """
    original_height, original_width, _ = frame.shape
    new_height, new_width = new_shape
    # Calculate the scaling factors for height and width
    scale_height = new_height / original_height
    scale_width = new_width / original_width
    scale_ = min(scale_height, scale_width)
    if scale_ == 1:
        return frame
    new_height = int(original_height * scale_)
    if new_height == 0:
        new_height = 1
    new_width = int(original_width * scale_)
    if new_width == 0:
        new_width = 1
    # note: cv2.resize uses WIDTH, HEIGHT order, instead of frames HEIGHT, WIDTH order
    return cv2.resize(frame, (new_width, new_height))
