import os
import threading
from typing import List

import gfpgan
from gfpgan import GFPGANer  # type: ignore[attr-defined]

from sinner.face_analyser import FaceAnalyser
from sinner.processors.BaseValidatedClass import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.State import State
from sinner.typing import Frame
from sinner.utilities import conditional_download, get_app_dir, is_image, is_video


class FaceEnhancer(BaseFrameProcessor):
    target: str
    output: str

    thread_semaphore = threading.Semaphore()
    thread_lock = threading.Lock()

    def rules(self) -> Rules:
        return super().rules() + [
            {'parameter': 'target', 'required': True, 'valid': lambda: is_image(self.target) or is_video(self.target)},
            {'parameter': 'output', 'default': self.suggest_output_path(), 'valid': os.path.isabs(self.output)},
            {'parameter': 'many-faces', 'default': False, 'action': True},
        ]

    def suggest_output_path(self) -> str:
        target_name, target_extension = os.path.splitext(os.path.basename(self.target))
        if self.output is None:
            return os.path.join(os.path.dirname(self.target), 'enhanced-' + target_name + target_extension)
        if os.path.isdir(self.output):
            return os.path.join(self.output, 'enhanced-' + target_name + target_extension)
        return self.output

    def __init__(self, execution_providers: List[str], execution_threads: int, max_memory: int, state: State):
        download_directory_path = get_app_dir('models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/GFPGANv1.4.pth'])
        super().__init__(execution_providers=execution_providers, execution_threads=execution_threads, max_memory=max_memory, state=state)
        self._face_enhancer = self.get_face_enhancer()
        self._face_analyser = FaceAnalyser(self.execution_providers)

    def get_face_enhancer(self) -> GFPGANer:
        with self.thread_lock:
            model_path = get_app_dir('models/GFPGANv1.4.pth')
            return gfpgan.GFPGANer(model_path=model_path, upscale=1)  # type: ignore[attr-defined]

    def enhance_face(self, temp_frame: Frame) -> Frame:
        with self.thread_semaphore:
            _, _, temp_frame = self._face_enhancer.enhance(temp_frame)
        return temp_frame

    def process_frame(self, temp_frame: Frame) -> Frame:
        if self._face_analyser.get_one_face(temp_frame):
            temp_frame = self.enhance_face(temp_frame)
        return temp_frame
