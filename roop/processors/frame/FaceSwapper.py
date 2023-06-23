import threading
from typing import List, Iterable, Any, Union

import insightface
from tqdm import tqdm
from roop.face_analyser import FaceAnalyser
from roop.handlers.video import BaseVideoHandler
from roop.parameters import Parameters
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.state import State
from roop.typing import Face, Frame, FaceSwapperType
from roop.utilities import is_image, resolve_relative_path, conditional_download, update_status, write_image, read_image


class FaceSwapper(BaseFrameProcessor):
    source: None | str = None  # none | file path
    many_faces: bool = False
    state: State

    _face_analyser: FaceAnalyser
    _face_swapper: FaceSwapperType
    _source_face: None | Face

    THREAD_LOCK = threading.Lock()

    def __init__(self, params: Parameters, state: State):
        download_directory_path = resolve_relative_path('../models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/inswapper_128.onnx'])
        self._face_analyser = FaceAnalyser(self.execution_providers)
        super().__init__(params)
        self.many_faces = params.many_faces
        self.state = state
        self._face_swapper = insightface.model_zoo.get_model(resolve_relative_path('../models/inswapper_128.onnx'), providers=self.execution_providers)

    def validate(self) -> bool:
        if not is_image(self.source):
            update_status('Select an image for source path.')
            return False
        self._source_face = self._face_analyser.get_one_face(read_image(self.source))
        if not self._source_face:
            update_status('No face in source path detected.')
            return False
        return True

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

    def process_frames(self, frames: Iterable, progress: None | tqdm = None) -> None:
        frame_type: None | int = None
        frame: str | tuple[Frame, int]
        for frame in frames:
            try:
                if None == frame_type: frame_type = self.FT_PATH if isinstance(frame, str) else self.FT_FRAME_TUPLE
                if self.FT_PATH == frame_type:
                    write_image(self.process_frame(read_image(frame)), self.state.get_frame_processed_name(frame))
                    self.state.set_processed(frame)
                else:
                    write_image(self.process_frame(frame[0]), self.state.get_frame_processed_name(str(frame[1] + 1).zfill(4) + '.png'))  # todo
            except Exception as exception:
                print(exception)
                pass
            if progress:
                progress.update(1)

    def process(self, frames_provider: BaseVideoHandler):
        update_status(f'Temp resources for this target already exists with {self.state.processed_frames_count()} frames processed, continue processing...')
        progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
        total = self.state.frames_count
        with tqdm(total=total, desc='Processing', unit='frame', dynamic_ncols=True, bar_format=progress_bar_format, initial=self.state.processed_frames_count()) as progress:
            progress.set_postfix({'execution_providers': self.execution_providers, 'threads': self.execution_threads, 'memory': self.max_memory})
            frames_provider.current_frame_index = self.state.processed_frames_count()
            self.multi_process_frame(frames_provider, self.process_frames, progress)
