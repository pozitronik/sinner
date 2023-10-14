import contextlib
import threading
from argparse import Namespace

import gfpgan
import torch
from gfpgan import GFPGANer  # type: ignore[attr-defined]

from sinner.FaceAnalyser import FaceAnalyser
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import conditional_download, get_app_dir, is_float


class FaceEnhancer(BaseFrameProcessor):
    emoji: str = '👍'

    thread_semaphore = threading.Semaphore()
    thread_lock = threading.Lock()

    upscale: float
    less_output: bool = True

    _face_analyser: FaceAnalyser | None = None
    _face_enhancer: GFPGANer | None = None

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'less-output',
                'default': True,
                'help': 'Silence noisy runtime console output'
            },
            {
                'parameter': {'upscale'},
                'attribute': 'upscale',
                'default': 1,
                'valid': lambda attribute, value: is_float(value),
                'help': 'Select the upscale factor for FaceEnhancer'
            },
            {
                'module_help': 'This module enhances faces on images'
            }
        ]

    @property
    def face_analyser(self) -> FaceAnalyser:
        if self._face_analyser is None:
            self._face_analyser = FaceAnalyser(self.execution_providers, self.less_output)
        return self._face_analyser

    @property
    def face_enhancer(self) -> GFPGANer:
        if self._face_enhancer is None:
            model_path = get_app_dir('models/GFPGANv1.4.pth')
            with self.thread_lock:
                if self.less_output:
                    with contextlib.redirect_stdout(None):
                        self._face_enhancer = gfpgan.GFPGANer(model_path=model_path, upscale=self.upscale)  # type: ignore[attr-defined]
                else:
                    self._face_enhancer = gfpgan.GFPGANer(model_path=model_path, upscale=self.upscale)  # type: ignore[attr-defined]
        return self._face_enhancer

    def __init__(self, parameters: Namespace) -> None:
        download_directory_path = get_app_dir('models')
        conditional_download(download_directory_path, ['https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth'])
        super().__init__(parameters)

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
