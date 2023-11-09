import glob
import importlib.util
import inspect
import mimetypes
import os
import platform
import shutil
import sys
import urllib
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Any, get_type_hints, Callable

import onnxruntime
import psutil
import tensorflow
from psutil import WINDOWS, MACOS
from tqdm import tqdm

TEMP_DIRECTORY = 'temp'


def limit_resources(max_memory: int) -> None:
    # prevent tensorflow memory leak
    gpus = tensorflow.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tensorflow.config.experimental.set_memory_growth(gpu, True)
    # limit memory usage
    if max_memory:
        memory = max_memory * 1024 ** 3
        if MACOS:
            memory = max_memory * 1024 ** 6
        if WINDOWS:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))  # type: ignore[attr-defined]


def path_exists(path: str) -> bool:
    norm_path = normalize_path(path)
    return os.path.exists(norm_path) if norm_path else False


def is_file(path: str) -> bool:
    norm_path = normalize_path(path)
    return os.path.isfile(norm_path) if norm_path else False


def is_dir(path: str) -> bool:
    norm_path = normalize_path(path)
    return os.path.isdir(norm_path) if norm_path else False


# todo test
def get_directory_file_list(directory_path: str, filter_: Callable[[str], bool] | None = None) -> List[str]:
    result: List[str] = []
    if is_dir(directory_path):
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if filter_:
                    if filter_(file_path) is True:
                        result.append(file_path)
                else:
                    result.append(file_path)
    return result


def is_image(image_path: str | None) -> bool:
    if image_path is not None and image_path and is_file(image_path):
        mimetype, _ = mimetypes.guess_type(image_path)
        return bool(mimetype and mimetype.startswith('image/'))
    return False


def is_video(video_path: str | None) -> bool:
    if video_path is not None and is_file(video_path):
        mimetype, _ = mimetypes.guess_type(video_path)
        return bool(mimetype and (mimetype.startswith('frame/') or mimetype.startswith('video/')))
    return False


def normalize_path(path: Any) -> str | None:
    if path is None:
        return None
    return os.path.normpath(os.path.expandvars(os.path.expanduser(path)))


def conditional_download(download_directory_path: str, urls: List[str], desc: str = 'Downloading') -> None:
    Path(download_directory_path).mkdir(parents=True, exist_ok=True)
    for url in urls:
        download_file_path = os.path.join(download_directory_path, os.path.basename(url))
        if not path_exists(download_file_path):
            request = urllib.request.urlopen(url)  # type: ignore[attr-defined]
            total = int(request.headers.get('Content-Length', 0))
            with tqdm(total=total, desc=desc, unit='B', unit_scale=True, unit_divisor=1024) as progress:
                urllib.request.urlretrieve(url, download_file_path, reporthook=lambda count, block_size, total_size: progress.update(block_size))  # type: ignore[attr-defined]


def resolve_relative_path(path: str, from_file: str | None = None) -> str:
    if from_file is None:
        try:
            current_frame = inspect.currentframe()
            if current_frame is not None:
                from_file = current_frame.f_back.f_code.co_filename  # type: ignore[union-attr]
        except Exception:
            raise Exception("Can't find caller method")
    return os.path.abspath(os.path.join(os.path.dirname(from_file), path))  # type: ignore[arg-type]


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
        if path_exists(module_path):
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
        module_name = get_file_name(file)
        if module_name == '__init__':
            continue
        descendant = load_class(os.path.dirname(file), module_name)
        if descendant is not None and class_name in get_all_base_names(descendant):
            result.append(module_name)
    return result


def get_all_base_names(search_class: type) -> List[str]:
    base_names = [base.__name__ for base in search_class.__bases__]
    for base in search_class.__bases__:
        base_names.extend(get_all_base_names(base))
    return base_names


def get_app_dir(sub_path: str = '') -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), sub_path)


def get_file_name(file_path: str) -> str:
    return os.path.splitext(os.path.basename(file_path))[0]


# unused
def delete_subdirectories(root_dir: str, subdirectories: List[str]) -> None:
    for subdirectory in list(set(subdirectories)):
        shutil.rmtree(subdirectory, ignore_errors=True)
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for directory in dirs:
            dir_path = os.path.join(root, directory)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)


def suggest_execution_threads() -> int:
    return 1


def suggest_max_memory() -> int:
    if platform.system().lower() == 'darwin':
        return 4
    return 16


def encode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers]


def decode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [provider for provider, encoded_execution_provider in zip(onnxruntime.get_available_providers(), encode_execution_providers(onnxruntime.get_available_providers()))
            if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers)]


def suggest_execution_providers() -> List[str]:
    return encode_execution_providers(onnxruntime.get_available_providers())


# returns the declared type of class attribute or None, if attribute isn't declared
def declared_attr_type(obj: object, attribute: str) -> Any:
    declared_typed_variables = get_type_hints(obj.__class__)
    if attribute in declared_typed_variables:
        return declared_typed_variables[attribute]
    return None


# this method considers windows root paths (e.g. c:) as absolute
def is_absolute_path(path: str) -> bool:
    return os.path.isabs(path) or (len(path) >= 2 and path[1] == ':' and path[0].isalpha())


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def format_sequences(sorted_list: List[int]) -> str:
    def format_sequence(s_start: int, s_end: int) -> str:
        return str(start) if s_start == s_end else f"{start}..{end}"

    sequences = []
    start = end = sorted_list[0]

    for num in sorted_list[1:]:
        if num == end + 1:
            end = num
        else:
            sequences.append(format_sequence(start, end))
            start = end = num

    sequences.append(format_sequence(start, end))
    return ", ".join(sequences)


def suggest_temp_dir(initial: str | None = None) -> str:
    if initial:
        norm_path = normalize_path(initial)
        if norm_path:
            return norm_path
        else:
            raise Exception(f"{initial} is not a valid path")
    return os.path.join(get_app_dir(), TEMP_DIRECTORY)


# calculates iteration median using previous calculated median, current iteration value and iteration counter
def iteration_mean(current_value: float, previous_value: float, iteration: int) -> float:
    return current_value if iteration == 0 else (previous_value * iteration + current_value) / (iteration + 1)


def seconds_to_hmsms(seconds: float) -> str:
    time_format = datetime.utcfromtimestamp(seconds).strftime("%H:%M:%S.%f")
    return time_format[:-3]  # Remove the last three digits to get milliseconds
