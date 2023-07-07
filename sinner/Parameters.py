import glob
import os
import platform
import warnings
from argparse import ArgumentParser, Namespace
from typing import List

import onnxruntime

from sinner.handlers.frame.FFmpegVideoHandler import FFmpegVideoHandler
from sinner.utilities import list_class_descendants, resolve_relative_path, is_image, is_video, update_status, get_app_dir, TEMP_DIRECTORY, get_file_name


class Parameters:
    SIGNATURE: str = 'def register_arguments(args: List[str]) -> None'
    parser: ArgumentParser = ArgumentParser(prog='😈sinner')
    parameters: Namespace

    def __init__(self):
        self.init_main_arguments()
        args, unknown_args = self.parser.parse_known_args()
        for argument in unknown_args:
            key, value = self.parse_argument(argument)
            setattr(args, key, value)
        self.parameters = args
        self.parameters.execution_provider = self.decode_execution_providers(self.parameters.execution_provider)
        self.output_path = self.normalize_output_path(self.parameters.source_path, self.parameters.target_path, args.output_path)

    def list_modules(self) -> List[str]:
        module_files = glob.glob('*.py', recursive=True)
        modules = []
        for file in module_files:
            if self.acceptable_for_loading(file):
                modules.append(file)
        return modules

    def acceptable_for_loading(self, file_path: str):
        with open(file_path, 'r') as file:
            for line in file:
                if self.SIGNATURE in line:
                    return True
        return False

    @staticmethod
    def parse_argument(argument: str) -> tuple[str, str] | tuple[str, list[str]] | None:  # key and list of values
        if not argument.startswith('--'):
            return None
        if '=' in argument:  # '--key=value'
            key, value = argument[2:].split('=')
            return key, value
        else:  # '--key value1 value2'
            key, value = argument[2:].split('=')
            value = value.split()
            return key, value

    def init_main_arguments(self):
        self.parser.add_argument('--frame-processor', help='pipeline of frame processors', dest='frame_processor', default=['FaceSwapper'],
                                 choices=list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor'), nargs='+')
        self.parser.add_argument('--source', help='select an source', dest='source_path', default=None)
        self.parser.add_argument('--target', help='select an target', dest='target_path', default=None)
        self.parser.add_argument('--output', help='select output file or directory', dest='output_path', default=None)
        self.parser.add_argument('--frame-handler', help='frame engine', dest='frame_handler', default=None, choices=list_class_descendants(resolve_relative_path('handlers/frame'), 'BaseFrameHandler'))
        self.parser.add_argument('--fps', help='set output frame fps', dest='fps', default=None)
        self.parser.add_argument('--keep-audio', help='keep original audio', dest='keep_audio', action='store_true', default=True)
        self.parser.add_argument('--keep-frames', help='keep temporary frames', dest='keep_frames', action='store_true', default=False)
        self.parser.add_argument('--many-faces', help='process every face', dest='many_faces', action='store_true', default=False)
        self.parser.add_argument('--max-memory', help='limit of RAM usage in GB', dest='max_memory', type=int, default=self.suggest_max_memory())
        self.parser.add_argument('--execution-provider', help='execution provider', dest='execution_provider', default=['cpu'], choices=self.suggest_execution_providers(), nargs='+')
        self.parser.add_argument('--execution-threads', help='number of execution threads', dest='execution_threads', type=int, default=self.suggest_execution_threads())
        self.parser.add_argument('--extract-frames', help='extract video frames before processing', dest='extract_frames', default=False, action='store_true')
        self.parser.add_argument('--gui', help='start in GUI mode', dest='gui', default=False, action='store_true')
        self.parser.add_argument('--temp-dir', help='temp directory', dest='temp_dir', default=None)
        self.parser.add_argument('--benchmark', help='run a benchmark on a selected frame processor', dest='benchmark', default=None)

    @staticmethod
    def default_frame_processors() -> List[str]:
        return ["CPUExecutionProvider"]

    @staticmethod
    def suggest_max_memory() -> int:
        if platform.system().lower() == 'darwin':
            return 4
        return 16

    @staticmethod
    def suggest_execution_threads() -> int:
        return 1

    @staticmethod
    def encode_execution_providers(execution_providers: List[str]) -> List[str]:
        return [execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers]

    def decode_execution_providers(self, execution_providers: List[str]) -> List[str]:
        return [provider for provider, encoded_execution_provider in zip(onnxruntime.get_available_providers(), self.encode_execution_providers(onnxruntime.get_available_providers()))
                if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers)]

    def suggest_execution_providers(self) -> List[str]:
        return self.encode_execution_providers(onnxruntime.get_available_providers())

    def set_frame_handler(self, preferred_handler: str | None = None) -> str:
        if self.parameters.benchmark:
            return ''  # todo
        if os.path.isdir(self.parameters.target_path):
            return 'DirectoryHandler'
        if is_image(self.parameters.target_path):
            return 'ImageHandler'
        if is_video(self.parameters.target_path):
            if preferred_handler is None:
                return 'VideoHandler' if FFmpegVideoHandler.available() else 'CV2VideoHandler'
            else:
                if preferred_handler == 'FFmpegVideoHandler' and not FFmpegVideoHandler.available():
                    warnings.warn("ffmpeg is not available in your system, falling back to cv2 handler", category=Warning)
                    return 'CV2VideoHandler'
        return preferred_handler  # type: ignore[return-value]

    def validate(self) -> bool:  # todo: it'll validate also for used processors
        if self.parameters.benchmark:
            return True
        if not is_image(self.parameters.source_path):
            update_status('Select an image for source path.')
            return False
        if not is_image(self.parameters.target_path) and not is_video(self.parameters.target_path) and not os.path.isdir(self.parameters.target_path):
            update_status('Select an image or video or images directory for target path.')
            return False
        return True

    def suggest_temp_dir(self, temp_dir: str | None) -> str:
        if self.parameters.benchmark:
            return ''
        return temp_dir if temp_dir is not None else os.path.join(os.path.dirname(self.parameters.target_path), get_app_dir(), TEMP_DIRECTORY)

    # todo: in some cases source_path can be empty, i need to fix it when implement processors validations
    @staticmethod
    def normalize_output_path(source_path: str, target_path: str, output_path: str | None) -> str:
        if source_path and target_path:
            if output_path is None:
                output_path = os.path.dirname(target_path)
            source_name = get_file_name(source_path)
            target_name, target_extension = os.path.splitext(os.path.basename(target_path))
            if os.path.isdir(output_path):
                return os.path.join(output_path, source_name + '-' + target_name + target_extension)
        return output_path  # type: ignore[return-value]
