import threading
from typing import List

import gfpgan
from gfpgan import GFPGANer  # type: ignore[attr-defined]

from sinner.face_analyser import FaceAnalyser
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.state import State
from sinner.typing import Frame
from sinner.utilities import resolve_relative_path, conditional_download


class FaceEnhancer(BaseFrameProcessor):
    thread_semaphore = threading.Semaphore()
    thread_lock = threading.Lock()

    def __init__(self, execution_providers: List[str], execution_threads: int, max_memory: int, state: State):
        download_directory_path = resolve_relative_path('../models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/sinner/resolve/main/GFPGANv1.4.pth'])
        super().__init__(execution_providers=execution_providers, execution_threads=execution_threads, max_memory=max_memory, state=state)
        self._face_enhancer = self.get_face_enhancer()
        self._face_analyser = FaceAnalyser(self.execution_providers)

    def get_face_enhancer(self) -> GFPGANer:
        with self.thread_lock:
            model_path = resolve_relative_path('../models/GFPGANv1.4.pth')
            return gfpgan.GFPGANer(model_path=model_path, upscale=1)  # type: ignore[attr-defined]

    def enhance_face(self, temp_frame: Frame) -> Frame:
        with self.thread_semaphore:
            _, _, temp_frame = self._face_enhancer.enhance(temp_frame)
        return temp_frame

    def process_frame(self, temp_frame: Frame) -> Frame:
        if self._face_analyser.get_one_face(temp_frame):
            temp_frame = self.enhance_face(temp_frame)
        return temp_frame
