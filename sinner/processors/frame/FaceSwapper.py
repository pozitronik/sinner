import os
from argparse import Namespace

import insightface

from sinner.face_analyser import FaceAnalyser
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.State import State
from sinner.typing import Face, Frame, FaceSwapperType
from sinner.utilities import conditional_download, read_image, get_app_dir, is_image, is_video, get_file_name


class FaceSwapper(BaseFrameProcessor):
    source_path: str = None
    target_path: str = None
    output_path: str = None
    many_faces: bool = False

    source_face: Face
    _face_analyser: FaceAnalyser
    _face_swapper: FaceSwapperType

    def rules(self) -> Rules:
        return super().rules() + [
            {'parameter': 'source_path', 'required': True, 'valid': is_image(self.source_path)},
            {'parameter': 'target_path', 'required': True, 'valid': is_image(self.target_path) or is_video(self.target_path) or os.path.isdir(self.target_path)},
            {'parameter': 'output_path', 'default': self.suggest_output_path(), 'valid': os.path.isabs(self.output_path)},
            {'parameter': 'many-faces', 'default': False, 'action': True},
        ]

    def suggest_output_path(self) -> str:
        source_name = get_file_name(self.source_path)
        target_name, target_extension = os.path.splitext(os.path.basename(self.target_path))
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), source_name + '-' + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, source_name + '-' + target_name + target_extension)
        return self.output_path

    def __init__(self, parameters: Namespace, state: State):
        download_directory_path = get_app_dir('models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/inswapper_128.onnx'])
        super().__init__(parameters=parameters, state=state)
        self._face_analyser = FaceAnalyser(self.execution_provider)
        self.source_face = self._face_analyser.get_one_face(read_image(self.source_path))
        self._face_swapper = insightface.model_zoo.get_model(get_app_dir('models/inswapper_128.onnx'), providers=self.execution_provider)

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
