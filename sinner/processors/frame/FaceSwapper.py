import contextlib
from argparse import Namespace
from typing import List, Dict, Any

import insightface
import torch

from sinner.FaceAnalyser import FaceAnalyser
from sinner.Status import Mood
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Face, Frame, FaceSwapperType
from sinner.utilities import conditional_download, get_app_dir, is_image


class FaceSwapper(BaseFrameProcessor):
    emoji: str = '🔁'

    source_path: str
    many_faces: bool = False
    less_output: bool = True

    _source_face: Face | None = None
    _face_analyser: FaceAnalyser | None = None
    _face_swapper: FaceSwapperType | None = None

    def rules(self) -> Rules:
        super().rules()
        return [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path',
                'required': True,
                'valid': lambda attribute_name, attribute_value: is_image(attribute_value),
                'help': 'Select an input image with the source face'
            },
            {
                'parameter': 'many-faces',
                'default': False,
                'help': 'Enable every face processing in the target'
            },
            {
                'parameter': 'less-output',
                'default': True,
                'action': True,
                'help': 'Silence noisy runtime console output'
            },
            {
                'module_help': 'This module swaps faces on images'
            }
        ]

    def load(self, parameters: Namespace, validate: bool = True) -> bool:
        self._source_face = None
        return super().load(parameters, validate)

    @property
    def source_face(self) -> Face | None:
        if self._source_face is None:
            self._source_face = self.face_analyser.get_one_face(CV2VideoHandler.read_image(self.source_path))
            if self._source_face is None:
                self.update_status(f"There is no face found on {self.source_path}", mood=Mood.BAD)
            else:
                face_data: List[Dict[str, Any]] = [
                    {"Age": self._source_face.age},
                    {"Sex": self._source_face.sex},
                    {"det_score": self._source_face.det_score},
                ]
                face_info = "\n".join([f"\t{key}: {value}" for dict_line in face_data for key, value in dict_line.items()])
                self.update_status(f'Recognized face:\n{face_info}')
        return self._source_face

    @property
    def face_analyser(self) -> FaceAnalyser:
        if self._face_analyser is None:
            self._face_analyser = FaceAnalyser(self.execution_providers, self.less_output)
        return self._face_analyser

    @property
    def face_swapper(self) -> FaceSwapperType:
        if self._face_swapper is None:
            if self.less_output:
                with contextlib.redirect_stdout(None):
                    self._face_swapper = insightface.model_zoo.get_model(get_app_dir('models/inswapper_128.onnx'), providers=self.execution_providers)
            else:
                self._face_swapper = insightface.model_zoo.get_model(get_app_dir('models/inswapper_128.onnx'), providers=self.execution_providers)
        return self._face_swapper

    def __init__(self, parameters: Namespace) -> None:
        download_directory_path = get_app_dir('models')
        conditional_download(download_directory_path, ['https://github.com/pozitronik/sinner/releases/download/v200823/inswapper_128.onnx'])
        super().__init__(parameters)

    def process_frame(self, frame: Frame) -> Frame:
        if self.many_faces:
            many_faces = self.face_analyser.get_many_faces(frame)
            if many_faces:
                for target_face in many_faces:
                    frame = self.face_swapper.get(frame, target_face, self.source_face)
        else:
            target_face = self.face_analyser.get_one_face(frame)
            if target_face:
                frame = self.face_swapper.get(frame, target_face, self.source_face)
        return frame

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.execution_providers:
            torch.cuda.empty_cache()
