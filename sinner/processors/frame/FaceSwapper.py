import os
from argparse import Namespace

import insightface

from sinner.face_analyser import FaceAnalyser
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Face, Frame, FaceSwapperType
from sinner.utilities import conditional_download, read_image, get_app_dir, is_image, is_video, get_file_name


class FaceSwapper(BaseFrameProcessor):
    source_path: str
    many_faces: bool = False

    _source_face: Face | None = None
    _face_analyser: FaceAnalyser | None = None
    _face_swapper: FaceSwapperType | None = None

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path',
                'required': True,
                'valid': lambda attribute_name, attribute_value: is_image(attribute_value),
                'help': 'Select a input image with the source face'
            },
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
                'valid': lambda attribute_name, attribute_value: attribute_value is not None and os.path.isabs(attribute_value),
                'help': 'Select an output file or a directory'
            },
            {
                'parameter': 'many-faces',
                'default': False,
                'action': True,
                'help': 'Enable every face processing in the target'
            },
        ]

    def suggest_output_path(self) -> str:
        source_name = get_file_name(self.source_path)
        target_name, target_extension = os.path.splitext(os.path.basename(self.target_path))
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), source_name + '-' + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, source_name + '-' + target_name + target_extension)
        return self.output_path

    @property
    def source_face(self) -> Face | None:
        if self._source_face is None:
            self._source_face = self.face_analyser.get_one_face(read_image(self.source_path))
        return self._source_face

    @property
    def face_analyser(self) -> FaceAnalyser:
        if self._face_analyser is None:
            self._face_analyser = FaceAnalyser(self.execution_providers)
        return self._face_analyser

    @property
    def face_swapper(self) -> FaceSwapperType:
        if self._face_swapper is None:
            self._face_swapper = insightface.model_zoo.get_model(get_app_dir('models/inswapper_128.onnx'), providers=self.execution_providers)
        return self._face_swapper

    def __init__(self, parameters: Namespace):
        download_directory_path = get_app_dir('models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/inswapper_128.onnx'])
        super().__init__(parameters=parameters)

    def process_frame(self, temp_frame: Frame) -> Frame:
        if self.many_faces:
            many_faces = self.face_analyser.get_many_faces(temp_frame)
            if many_faces:
                for target_face in many_faces:
                    temp_frame = self.face_swapper.get(temp_frame, target_face, self.source_face)
        else:
            target_face = self.face_analyser.get_one_face(temp_frame)
            if target_face:
                temp_frame = self.face_swapper.get(temp_frame, target_face, self.source_face)
        return temp_frame
