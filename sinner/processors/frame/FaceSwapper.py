import contextlib
import io
import os
import threading
from argparse import Namespace
from typing import List, Dict, Any, Callable, Literal

import insightface
import torch
from insightface.app.common import Face

from sinner.FaceAnalyser import FaceAnalyser
from sinner.models.logger.Status import Mood
from sinner.helpers.FrameHelper import read_from_image
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame, FaceSwapperType
from sinner.utilities import conditional_download, get_app_dir, is_image, normalize_path


class FaceSwapper(BaseFrameProcessor):
    emoji: str = '🔁'

    source_path: str
    many_faces: bool = False
    less_output: bool = True
    target_gender: Literal['M', 'F', 'B', 'I'] = 'B'

    _source_face: Face | None = None
    _face_analyser: FaceAnalyser | None = None
    _face_swapper: FaceSwapperType | None = None

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path',
                'required': False,
                'valid': lambda attribute_name, attribute_value: is_image(attribute_value),
                'filter': lambda: normalize_path(self.source_path),
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
                'parameter': {'target-gender', 'gender'},
                'attribute': 'target_gender',
                'default': 'I',
                'choices': ['M', 'F', 'B', 'I'],
                'help': 'Select the gender of faces to swap: [M]ale, [F]emale, [B]oth, or as_[I]nput (based on source face)'
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
            if self.source_path is None:
                # self.update_status(f"There is no source path is provided, ignoring", mood=Mood.BAD)
                return self._source_face
            self._source_face = self.face_analyser.get_one_face(read_from_image(self.source_path))
            if self._source_face is None:
                self.update_status(f"There is no face found on {self.source_path}", mood=Mood.BAD)
            else:
                face_data: List[Dict[str, Any]] = [
                    {"Age": self._source_face.age},
                    {"Sex": self._source_face.sex},
                    {"det_score": self._source_face.det_score},
                ]
                face_info = "\n".join([f"\t{key}: {value}" for dict_line in face_data for key, value in dict_line.items()])
                self.update_status(f'Recognized source face:\n{face_info}')
        return self._source_face

    @property
    def face_analyser(self) -> FaceAnalyser:
        if self._face_analyser is None:
            self._face_analyser = FaceAnalyser(self.execution_providers, self.less_output)
        return self._face_analyser

    @property
    def face_swapper(self) -> FaceSwapperType:
        if self._face_swapper is None:
            with threading.Lock():
                if self.less_output:
                    with contextlib.redirect_stdout(io.StringIO()):
                        self._face_swapper = insightface.model_zoo.get_model(get_app_dir('models/inswapper_128.onnx'), providers=self.execution_providers)
                else:
                    self._face_swapper = insightface.model_zoo.get_model(get_app_dir('models/inswapper_128.onnx'), providers=self.execution_providers)
        return self._face_swapper

    def __init__(self, parameters: Namespace) -> None:
        download_directory_path = get_app_dir('models')
        conditional_download(download_directory_path, ['https://github.com/pozitronik/sinner/releases/download/v200823/inswapper_128.onnx'])
        super().__init__(parameters)

        if self.source_path is None:
            self.update_status("No source path is set, assuming GUI mode bootstrap", mood=Mood.NEUTRAL)
            _, _, _ = self.face_analyser, self.face_swapper, self.face_analyser.face_analyser

    def process_frame(self, frame: Frame) -> Frame:
        if self.source_face is not None:
            target_gender = self._get_target_gender()
            if self.many_faces:
                many_faces = self.face_analyser.get_many_faces(frame)
                if many_faces:
                    for target_face in many_faces:
                        if self._should_swap_face(target_face, target_gender):
                            frame = self.face_swapper.get(frame, target_face, self.source_face)
            else:
                target_face = self.face_analyser.get_one_face(frame)
                if target_face and self._should_swap_face(target_face, target_gender):
                    frame = self.face_swapper.get(frame, target_face, self.source_face)
        return frame

    def _get_target_gender(self) -> str:
        if self.target_gender == 'I' and self.source_face:
            return self.source_face.sex
        return self.target_gender

    def _should_swap_face(self, face: Face, target_gender: str) -> bool:
        if target_gender == 'B':
            return True
        if face.sex == target_gender:
            return True
        if face.sex not in ['M', 'F']:
            self.update_status("Unable to determine gender for a face. Skipping this face.", mood=Mood.NEUTRAL)
        return False

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.execution_providers:
            torch.cuda.empty_cache()

    def configure_output_filename(self, callback: Callable[[str], None]) -> None:
        source_name, _ = os.path.splitext(os.path.basename(self.source_path))
        callback(source_name)