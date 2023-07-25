from typing import List

from sinner.FaceAnalyser import FaceAnalyser
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.typing import Face
from tests.constants import source_jpg, target_faces


def get_test_object() -> FaceAnalyser:
    return FaceAnalyser(execution_providers=['CPUExecutionProvider'])


def test_one_face():
    analyser = get_test_object()
    face = analyser.get_one_face(CV2VideoHandler.read_image(source_jpg))
    assert (face, Face)
    assert face.age == 31
    assert face.sex == 'F'


def test_one_face_from_many():
    analyser = get_test_object()
    face = analyser.get_one_face(CV2VideoHandler.read_image(target_faces))
    assert (face, Face)
    assert face.age == 47
    assert face.sex == 'M'


def test_many_faces():
    analyser = get_test_object()
    faces = analyser.get_many_faces(CV2VideoHandler.read_image(target_faces))
    assert (faces, List)
    assert len(faces) == 2
    assert faces[0].age == 28
    assert faces[0].sex == 'F'
    assert faces[1].age == 47
    assert faces[1].sex == 'M'
