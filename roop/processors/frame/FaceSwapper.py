import threading
from typing import Iterable, List

import insightface
from tqdm import tqdm

from roop.face_analyser import FaceAnalyser
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.state import State
from roop.typing import Face, Frame, FaceSwapperType
from roop.utilities import resolve_relative_path, conditional_download, update_status, write_image


class FaceSwapper(BaseFrameProcessor):
    many_faces: bool = False
    state: State

    _face_analyser: FaceAnalyser
    _face_swapper: FaceSwapperType
    _source_face: None | Face

    THREAD_LOCK = threading.Lock()

    def __init__(self, execution_providers: List[str], execution_threads: int, max_memory: int, many_faces: bool, state: State):
        download_directory_path = resolve_relative_path('../models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/inswapper_128.onnx'])
        self._face_analyser = FaceAnalyser(self.execution_providers)
        super().__init__(execution_providers=execution_providers, execution_threads=execution_threads, max_memory=max_memory)
        self.many_faces = many_faces
        self.state = state
        self._face_swapper = insightface.model_zoo.get_model(resolve_relative_path('../models/inswapper_128.onnx'), providers=self.execution_providers)

    def swap_face(self, target_face: Face, temp_frame: Frame) -> Frame:
        return self._face_swapper.get(temp_frame, target_face, self._source_face, paste_back=True)

    def process_frame(self, temp_frame: Frame) -> Frame:
        if self.many_faces:
            many_faces = self._face_analyser.get_many_faces(temp_frame)
            if many_faces:
                for target_face in many_faces:
                    temp_frame = self.swap_face(target_face, temp_frame)
        else:
            target_face = self._face_analyser.get_one_face(temp_frame)
            if target_face:
                temp_frame = self.swap_face(target_face, temp_frame)
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
        update_status(f'Temp resources for this target already exists with {self.state.processed_frames_count()} frames processed, continue processing...')
        progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
        total = self.state.frames_count
        with tqdm(total=total, desc='Processing', unit='frame', dynamic_ncols=True, bar_format=progress_bar_format, initial=self.state.processed_frames_count()) as progress:
            progress.set_postfix({'execution_providers': self.execution_providers, 'threads': self.execution_threads, 'memory': self.max_memory})
            self.multi_process_frame(frames_provider, self.process_frames, progress)
