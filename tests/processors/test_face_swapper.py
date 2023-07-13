import multiprocessing
from argparse import Namespace

from sinner.Parameters import Parameters
from sinner.face_analyser import FaceAnalyser
from sinner.processors.frame.FaceSwapper import FaceSwapper
from sinner.State import State
from sinner.typing import Frame, FaceSwapperType, Face
from sinner.utilities import read_image
from tests.constants import source_jpg, target_png, IMAGE_SHAPE, tmp_dir

parameters: Namespace = Parameters(f'--execution-provider=cpu --execution-threads={multiprocessing.cpu_count()} --max-memory=12 --source-path="{source_jpg}" --target-path="{target_png}" --output-path="{tmp_dir}"').parameters


def get_test_state() -> State:
    return State(
        parameters=parameters,
        frames_count=1,
        temp_dir=tmp_dir
    )


def get_test_object() -> FaceSwapper:
    return FaceSwapper(parameters=parameters, state=get_test_state())


def test_init():
    test_object = get_test_object()
    assert (test_object, FaceSwapper)
    assert (test_object._face_analyser, FaceAnalyser)
    assert (test_object._face_swapper, FaceSwapperType)


def test_face_analysis():  # todo: move to face_analyser_test
    face = get_test_object().source_face
    assert (face, Face)
    assert face.age == 31
    assert face.sex == 'F'


def test_process_frame():
    processed_frame = get_test_object().process_frame(read_image(target_png))
    assert (processed_frame, Frame)
    assert processed_frame.shape == IMAGE_SHAPE
