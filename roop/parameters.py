import platform
from argparse import Namespace
from dataclasses import dataclass, field
from typing import List

import onnxruntime

from roop.utilities import normalize_output_path


def default_frame_processors():
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


@dataclass
class Parameters:
    source_path: None | str = None
    target_path: None | str = None
    output_path: None | str = None
    frame_processors: List[str] = field(default_factory=lambda: default_frame_processors())
    fps: None | float = None #  None for auto
    keep_audio: bool = True
    keep_frames: bool = False
    many_faces: bool = True
    max_memory: int = lambda: suggest_max_memory()
    execution_providers: List[str] = field(default_factory=lambda: suggest_execution_providers())
    execution_threads: int = lambda: suggest_execution_threads()

    def __init__(self, args: Namespace):
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