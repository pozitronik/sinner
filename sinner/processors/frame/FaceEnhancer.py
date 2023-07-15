import os
import threading
from argparse import Namespace

import gfpgan
from gfpgan import GFPGANer  # type: ignore[attr-defined]

from sinner.FaceAnalyser import FaceAnalyser
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import conditional_download, get_app_dir, is_image, is_video


class FaceEnhancer(BaseFrameProcessor):
    thread_semaphore = threading.Semaphore()
    thread_lock = threading.Lock()

    _face_analyser: FaceAnalyser | None = None
    _face_enhancer: GFPGANer | None = None

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'required': True,
                'valid': lambda: is_image(self.target_path) or is_video(self.target_path),
                'help': 'Select the target file (image or video) or the directory'
            },
            {
                'parameter': {'output', 'output-path'},
                'attribute': 'output_path',
                'default': lambda: self.suggest_output_path(),
                'valid': lambda: os.path.isabs(self.output_path),
                'help': 'Select an output file or a directory'
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
                self._face_enhancer = gfpgan.GFPGANer(model_path=model_path, upscale=1)  # type: ignore[attr-defined]
        return self._face_enhancer

    def __init__(self, parameters: Namespace):
        download_directory_path = get_app_dir('models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/GFPGANv1.4.pth'])
        super().__init__(parameters=parameters)

    def enhance_face(self, temp_frame: Frame) -> Frame:
        with self.thread_semaphore:
            _, _, temp_frame = self.face_enhancer.enhance(temp_frame)
        return temp_frame

    def process_frame(self, temp_frame: Frame) -> Frame:
        if self.face_analyser.get_one_face(temp_frame):
            temp_frame = self.enhance_face(temp_frame)
        return temp_frame
