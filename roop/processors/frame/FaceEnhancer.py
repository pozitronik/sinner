import threading
from typing import Iterable, List

import gfpgan
import insightface
from gfpgan import GFPGANer
from tqdm import tqdm

from roop.face_analyser import FaceAnalyser
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.state import State
from roop.typing import Frame
from roop.utilities import resolve_relative_path, conditional_download, update_status, get_mem_usage, write_image


class FaceEnhancer(BaseFrameProcessor):
    state: State
    many_faces: bool = False

    THREAD_SEMAPHORE = threading.Semaphore()
    THREAD_LOCK = threading.Lock()

    def __init__(self, execution_providers: List[str], execution_threads: int, max_memory: int, many_faces: bool, state: State):
        download_directory_path = resolve_relative_path('../models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/GFPGANv1.4.pth'])
        self._face_enhancer = self.get_face_enhancer()
        self._face_analyser = FaceAnalyser(self.execution_providers)

        super().__init__(execution_providers=execution_providers, execution_threads=execution_threads, max_memory=max_memory)
        self.many_faces = many_faces
        self.state = state
        self._face_swapper = insightface.model_zoo.get_model(resolve_relative_path('../models/inswapper_128.onnx'), providers=self.execution_providers)

    def get_face_enhancer(self) -> GFPGANer:
        with self.THREAD_LOCK:
            model_path = resolve_relative_path('../models/GFPGANv1.4.pth')
            return gfpgan.GFPGANer(model_path=model_path, upscale=1)

    def enhance_face(self, temp_frame: Frame) -> Frame:
        with self.THREAD_SEMAPHORE:
            _, _, temp_frame = self._face_enhancer.enhance(temp_frame)
        return temp_frame

    def process_frame(self, temp_frame: Frame) -> Frame:
        if self._face_analyser.get_one_face(temp_frame):
            temp_frame = self.enhance_face(temp_frame)
        return temp_frame

    def process_frames(self, frames: Iterable[tuple[Frame, int]], progress: None | tqdm = None) -> None:  # type: ignore[type-arg]
        for frame in frames:
            try:
                write_image(self.process_frame(frame[0]), self.state.get_frame_processed_name(frame[1]))
            except Exception as exception:
                print(exception)
                pass
            if progress is not None:
                progress.update()

    def process(self, frames_provider: Iterable[tuple[Frame, int]]) -> None:
        update_status(f'Temp resources for this target already exists with {self.state.processed_frames_count()} frames processed, continue processing...')  # todo optional
        progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
        total = self.state.frames_count
        with tqdm(total=total, desc='Processing', unit='frame', dynamic_ncols=True, bar_format=progress_bar_format, initial=self.state.processed_frames_count()) as progress:
            progress.set_postfix({
                'memory_usage': '{:.2f}'.format(get_mem_usage()).zfill(5) + 'MB',
                'execution_providers': self.execution_providers,
                'threads': self.execution_threads,
                'memory': self.max_memory
            })
            self.multi_process_frame(frames_provider, self.process_frames, progress)
