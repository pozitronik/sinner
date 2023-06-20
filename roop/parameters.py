import platform
from dataclasses import dataclass, field
from typing import List

import onnxruntime


def default_frame_processors():
    return ["CPUExecutionProvider"]


def suggest_max_memory() -> int:
    if platform.system().lower() == 'darwin':
        return 4
    return 16


def suggest_execution_threads() -> int:
    if 'DmlExecutionProvider' in Params.execution_providers:
        return 1
    if 'ROCMExecutionProvider' in Params.execution_providers:
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
    source_path: [None, str] = None
    target_path: [None, str] = None
    output_path: [None, str] = None
    frame_processors: List[str] = field(default_factory=lambda: default_frame_processors())
    keep_fps: bool = True
    keep_audio: bool = True
    keep_frames: bool = False
    many_faces: bool = True
    max_memory: int = lambda: suggest_max_memory()
    execution_providers: List[str] = field(default_factory=lambda: suggest_execution_providers())
    execution_threads: int = lambda: suggest_execution_threads()


Params = Parameters()
