import os
import threading
from argparse import Namespace

import gfpgan
import torch
from gfpgan import GFPGANer  # type: ignore[attr-defined]

from sinner.FaceAnalyser import FaceAnalyser
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import conditional_download, get_app_dir, is_image, is_video, is_absolute_path, is_float


class FaceEnhancer(BaseFrameProcessor):
    thread_semaphore = threading.Semaphore()
    thread_lock = threading.Lock()

    upscale: float

    _face_analyser: FaceAnalyser | None = None
    _face_enhancer: GFPGANer | None = None

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'required': True,
                'valid': lambda attribute_name, attribute_value: attribute_value is not None and (is_image(attribute_value) or is_video(attribute_value) or os.path.isdir(attribute_value)),
                'help': 'Select the target file (image or video) or the directory'
            },
            {
                'parameter': {'output', 'output-path'},
                'attribute': 'output_path',
                'default': lambda: self.suggest_output_path(),
                'valid': lambda: is_absolute_path(self.output_path),
                'help': 'Select an output file or a directory'
            },
            {
                'parameter': {'upscale'},
                'attribute': 'upscale',
                'default': 1,
                'valid': lambda attribute, value: is_float(value),
                'help': 'Select the upscale for FaceEnhancer'
            },
        ]

    def suggest_output_path(self) -> str:
        target_name, target_extension = os.path.splitext(os.path.basename(self.target_path))
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), 'enhanced-' + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, 'enhanced-' + target_name + target_extension)
        return self.output_path

    @property
    def face_analyser(self) -> FaceAnalyser:
        if self._face_analyser is None:
            self._face_analyser = FaceAnalyser(self.execution_providers)
        return self._face_analyser

    @property
    def face_enhancer(self) -> GFPGANer:
        if self._face_enhancer is None:
            with self.thread_lock:
                model_path = get_app_dir('models/GFPGANv1.4.pth')
                self._face_enhancer = gfpgan.GFPGANer(model_path=model_path, upscale=self.upscale)  # type: ignore[attr-defined]
        return self._face_enhancer

    def __init__(self, parameters: Namespace, target_path: str | None = None) -> None:
        download_directory_path = get_app_dir('models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/GFPGANv1.4.pth'])
        super().__init__(parameters, target_path)

    def enhance_face(self, temp_frame: Frame) -> Frame:
        with self.thread_semaphore:
            _, _, temp_frame = self.face_enhancer.enhance(temp_frame)
        return temp_frame

    def process_frame(self, frame: Frame) -> Frame:
        if self.face_analyser.get_one_face(frame):
            frame = self.enhance_face(frame)
        return frame

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.execution_providers:
            torch.cuda.empty_cache()
