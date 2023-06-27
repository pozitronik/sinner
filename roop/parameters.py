import argparse
import os.path
import platform
import warnings
from argparse import Namespace
from typing import List

import onnxruntime

from roop.handlers.frames.FFmpegVideoHandler import FFmpegVideoHandler
from roop.utilities import normalize_output_path, is_image, is_video, list_class_descendants, resolve_relative_path, update_status


def default_frame_processors() -> List[str]:
    return ["CPUExecutionProvider"]


def suggest_max_memory() -> int:
    if platform.system().lower() == 'darwin':
        return 4
    return 16


def suggest_execution_threads() -> int:
    if 'DmlExecutionProvider' in suggest_execution_providers():
        return 1
    if 'ROCMExecutionProvider' in suggest_execution_providers():
        return 2
    return 8


def encode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers]


def decode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [provider for provider, encoded_execution_provider in zip(onnxruntime.get_available_providers(), encode_execution_providers(onnxruntime.get_available_providers()))
            if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers)]


def suggest_execution_providers() -> List[str]:
    return encode_execution_providers(onnxruntime.get_available_providers())


def parse_args() -> Namespace:
    program = argparse.ArgumentParser()
    program.add_argument('-s', '--source', help='select an source image', dest='source_path')
    program.add_argument('-t', '--target', help='select an target image or frames', dest='target_path')
    program.add_argument('-o', '--output', help='select output file or directory', dest='output_path')
    program.add_argument('--frame-processor', help='pipeline of frame processors', dest='frame_processor', default=['FaceSwapper'],
                         choices=list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor'), nargs='+')
    program.add_argument('--frame-handler', help='frames engine', dest='frame_handler', default=None, choices=list_class_descendants(resolve_relative_path('handlers/frames'), 'BaseFramesHandler'))
    program.add_argument('--fps', help='set output frames fps', dest='fps', default=None)
    program.add_argument('--keep-audio', help='keep original audio', dest='keep_audio', action='store_true', default=True)
    program.add_argument('--keep-frames', help='keep temporary frames', dest='keep_frames', action='store_true', default=False)
    program.add_argument('--many-faces', help='process every face', dest='many_faces', action='store_true', default=False)
    program.add_argument('--max-memory', help='maximum amount of RAM in GB', dest='max_memory', type=int, default=suggest_max_memory())
    program.add_argument('--execution-provider', help='execution provider', dest='execution_provider', default=['cpu'], choices=suggest_execution_providers(), nargs='+')
    program.add_argument('--execution-threads', help='number of execution threads', dest='execution_threads', type=int, default=suggest_execution_threads())
    return program.parse_args()


class Parameters:
    source_path: str
    target_path: str
    output_path: str
    frame_processors: List[str]
    fps: float  # None for auto
    keep_audio: bool = True
    keep_frames: bool = False
    many_faces: bool = True
    max_memory: int
    execution_providers: List[str]
    execution_threads: int
    frame_handler: str

    def __init__(self, args: Namespace | None = None) -> None:
        args = parse_args() if args is None else args
        self.source_path = args.source_path
        self.target_path = args.target_path
        self.output_path = normalize_output_path(self.source_path, self.target_path, args.output_path)
        self.frame_processors = args.frame_processor
        self.headless = args.source_path or args.target_path or args.output_path
        self.fps = args.fps
        self.keep_audio = args.keep_audio
        self.keep_frames = args.keep_frames
        self.many_faces = args.many_faces
        self.max_memory = args.max_memory
        self.execution_providers = decode_execution_providers(args.execution_provider)
        self.execution_threads = args.execution_threads
        self.frame_handler = self.set_frame_handler(args.frame_handler)

        if not self.validate():
            quit()

    def set_frame_handler(self, preferred_handler: str | None = None) -> str:
        if os.path.isdir(self.target_path):
            return 'DirectoryHandler'
        if is_image(self.target_path):
            return 'ImageHandler'
        if is_video(self.target_path):
            if preferred_handler is None:
                return 'FFmpegVideoHandler' if FFmpegVideoHandler.available() else 'CV2VideoHandler'
            else:
                if preferred_handler == 'FFmpegVideoHandler' and not FFmpegVideoHandler.available():
                    warnings.warn("ffmpeg is not available in your system, falling back to cv2 handler", category=Warning)
                    return 'CV2VideoHandler'
        return preferred_handler  # type: ignore[return-value]

    def validate(self) -> bool:  # todo: it'll validate also for used processors
        if not is_image(self.source_path):
            update_status('Select an image for source path.')
            return False
        if not is_image(self.target_path) and not is_video(self.target_path) and not os.path.isdir(self.target_path):
            update_status('Select an image or video or images directory for target path.')
            return False
        return True
