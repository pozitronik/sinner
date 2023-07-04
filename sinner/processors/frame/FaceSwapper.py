from typing import List

import insightface

from sinner.face_analyser import FaceAnalyser
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.state import State
from sinner.typing import Face, Frame, FaceSwapperType
from sinner.utilities import conditional_download, read_image, get_app_dir


class FaceSwapper(BaseFrameProcessor):
    many_faces: bool = False
    source_face: Face

    _face_analyser: FaceAnalyser
    _face_swapper: FaceSwapperType

    def __init__(self, execution_providers: List[str], execution_threads: int, max_memory: int, many_faces: bool, source_path: str, state: State):
        download_directory_path = get_app_dir('models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/inswapper_128.onnx'])
        super().__init__(execution_providers=execution_providers, execution_threads=execution_threads, max_memory=max_memory, state=state)
        self._face_analyser = FaceAnalyser(self.execution_providers)
        self.many_faces = many_faces
        self.source_face = self._face_analyser.get_one_face(read_image(source_path))
        self._face_swapper = insightface.model_zoo.get_model(get_app_dir('models/inswapper_128.onnx'), providers=self.execution_providers)

    def process_frame(self, temp_frame: Frame) -> Frame:
        if self.many_faces:
            many_faces = self._face_analyser.get_many_faces(temp_frame)
            if many_faces:
                for target_face in many_faces:
                    temp_frame = self._face_swapper.get(temp_frame, target_face, self.source_face)
        else:
            target_face = self._face_analyser.get_one_face(temp_frame)
            if target_face:
                temp_frame = self._face_swapper.get(temp_frame, target_face, self.source_face)
        return temp_frame
