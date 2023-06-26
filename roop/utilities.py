import mimetypes
import os
import platform
import urllib
from typing import List, Literal

import cv2
import psutil
import tensorflow
from numpy import array, uint8, fromfile
from tqdm import tqdm

from roop.typing import Frame

TEMP_FILE = 'temp.mp4'
TEMP_DIRECTORY = 'temp'


def limit_resources(max_memory: int) -> None:
    # prevent tensorflow memory leak
    gpus = tensorflow.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tensorflow.config.experimental.set_memory_growth(gpu, True)
    # limit memory usage
    if max_memory:
        memory = max_memory * 1024 ** 3
        if platform.system().lower() == 'darwin':
            memory = max_memory * 1024 ** 6
        if platform.system().lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))  # type: ignore[attr-defined]


def update_status(message: str, caller: str = 'GLOBAL') -> None:
    print(f'[{caller}] {message}')


def get_temp_directory_path(target_path: str) -> str:
    target_name, _ = os.path.splitext(os.path.basename(target_path))
    target_directory_path = os.path.dirname(target_path)
    return os.path.join(target_directory_path, TEMP_DIRECTORY, target_name)


def normalize_output_path(source_path: str, target_path: str, output_path: str) -> str:
    if source_path and target_path:
        source_name, _ = os.path.splitext(os.path.basename(source_path))
        target_name, target_extension = os.path.splitext(os.path.basename(target_path))
        if os.path.isdir(output_path):
            return os.path.join(output_path, source_name + '-' + target_name + target_extension)
    return output_path


def is_image(image_path: str | None) -> bool:
    if image_path is not None and image_path and os.path.isfile(image_path):
        mimetype, _ = mimetypes.guess_type(image_path)
        return bool(mimetype and mimetype.startswith('image/'))
    return False


def is_video(video_path: str) -> bool:
    if video_path and os.path.isfile(video_path):
        mimetype, _ = mimetypes.guess_type(video_path)
        return bool(mimetype and (mimetype.startswith('frames/') or mimetype.startswith('video/')))
    return False


def conditional_download(download_directory_path: str, urls: List[str]) -> None:
    if not os.path.exists(download_directory_path):
        os.makedirs(download_directory_path)
    for url in urls:
        download_file_path = os.path.join(download_directory_path, os.path.basename(url))
        if not os.path.exists(download_file_path):
            request = urllib.request.urlopen(url)  # type: ignore[attr-defined]
            total = int(request.headers.get('Content-Length', 0))
            with tqdm(total=total, desc='Downloading', unit='B', unit_scale=True, unit_divisor=1024) as progress:
                urllib.request.urlretrieve(url, download_file_path, reporthook=lambda count, block_size, total_size: progress.update(block_size))  # type: ignore[attr-defined]


def resolve_relative_path(path: str, from_file: str = __file__) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(from_file), path))


def read_image(path: str) -> Frame:
    if platform.system().lower() == 'windows':  # issue #511
        image = cv2.imdecode(fromfile(path, dtype=uint8), cv2.IMREAD_UNCHANGED)
        if image.shape[2] == 4:  # fixes the alpha-channel issue
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        return image
    else:
        return cv2.imread(path)


def write_image(image: Frame, path: str) -> bool:
    if platform.system().lower() == 'windows':  # issue #511
        is_success, im_buf_arr = cv2.imencode(".png", image)
        im_buf_arr.tofile(path)
        return is_success
    else:
        return cv2.imwrite(path, array)


def get_mem_usage(size: Literal['b', 'k', 'm', 'g'] = 'm') -> int:
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss
    if size == 'b':
        return memory_usage
    if size == 'k':
        return memory_usage / 1024
    if size == 'm':
        return memory_usage / 1024**2
    if size == 'g':
        return memory_usage / 1024**3
