import threading
from typing import List
from insightface.app import FaceAnalysis

from roop.typing import Frame, Face


class FaceAnalyser:
    THREAD_LOCK = threading.Lock()

    _face_analyser: FaceAnalysis
    _execution_providers: List[str]

    def __init__(self, execution_providers: List[str]):
        self._execution_providers = execution_providers
        with self.THREAD_LOCK:
            self._face_analyser = FaceAnalysis(name='buffalo_l', providers=self._execution_providers)
            self._face_analyser.prepare(ctx_id=0, det_size=(640, 640))

    def get_one_face(self, frame: Frame) -> None | Face:
        face = self._face_analyser.get(frame)
        try:
            return min(face, key=lambda x: x.bbox[0])
        except ValueError:
            return None

    def get_many_faces(self, frame: Frame) -> None | List[Face]:
        try:
            return self._face_analyser.get(frame)
        except IndexError:
            return None
