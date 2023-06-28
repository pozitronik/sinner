import glob
import importlib.util
import mimetypes
import os
import platform
import sys
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


def normalize_output_path(source_path: str, target_path: str, output_path: str | None) -> str:
    if source_path and target_path:
        if output_path is None:
            output_path = os.path.dirname(target_path)
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


def conditional_download(download_directory_path: str, urls: List[str], desc: str = 'Downloading') -> None:
    if not os.path.exists(download_directory_path):
        os.makedirs(download_directory_path)
    for url in urls:
        download_file_path = os.path.join(download_directory_path, os.path.basename(url))
        if not os.path.exists(download_file_path):
            request = urllib.request.urlopen(url)  # type: ignore[attr-defined]
            total = int(request.headers.get('Content-Length', 0))
            with tqdm(total=total, desc=desc, unit='B', unit_scale=True, unit_divisor=1024) as progress:
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
        return cv2.imwrite(path, image)


def get_mem_usage(param: Literal['rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty'] = 'rss', size: Literal['b', 'k', 'm', 'g'] = 'm') -> int:
    """
    The `memory_info()` method of the `psutil.Process` class provides information about the memory usage of a process. It returns a named tuple containing the following attributes:

    - `rss`: Resident Set Size - the amount of non-swapped physical memory used by the process in bytes.
    - `vms`: Virtual Memory Size - the total amount of virtual memory used by the process in bytes.
    - `shared`: Shared Memory - the amount of shared memory used by the process in bytes.
    - `text`: Text (Code) Segment - the amount of memory used by the executable code of the process in bytes.
    - `data`: Data Segment - the amount of memory used by the data (initialized variables) of the process in bytes.
    - `lib`: Library (DLL) Segment - the amount of memory used by shared libraries and dynamically loaded modules in bytes.

    Note that the availability of these attributes may vary depending on the platform and system configuration.
    """
    process = psutil.Process(os.getpid())
    memory_usage = getattr(process.memory_info(), param)
    if size == 'b':
        return memory_usage
    if size == 'k':
        return memory_usage / 1024
    if size == 'm':
        return memory_usage / 1024 ** 2
    if size == 'g':
        return memory_usage / 1024 ** 3


def load_class(path: str, module_name: str, class_name: str | None = None) -> type | None:
    if class_name is None:
        class_name = module_name
    module_path = os.path.join(path, module_name + '.py')
    try:
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is not None:
                module = importlib.util.module_from_spec(spec)
                if module is not None and module_name not in sys.modules:
                    spec.loader.exec_module(module)  # type: ignore[union-attr]
                return getattr(module, class_name)
        return None
    except Exception:
        pass
        return None


def list_class_descendants(path: str, class_name: str) -> List['str']:
    """
    Return all class descendants in its directory
    """
    result: List[str] = []
    files_list = glob.glob(os.path.join(path, '*.py'))
    for file in files_list:
        module_name = os.path.splitext(os.path.basename(file))[0]
        if module_name == '__init__':
            continue
        descendant = load_class(os.path.dirname(file), module_name)
        if descendant and descendant.__base__.__name__ == class_name:  # issubclass will not work here
            result.append(module_name)
    return result
