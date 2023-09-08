import multiprocessing
from argparse import Namespace

from colorama import Fore, Back

from sinner.Parameters import Parameters
from sinner.FaceAnalyser import FaceAnalyser
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.processors.frame.FaceSwapper import FaceSwapper
from sinner.typing import Frame, FaceSwapperType, Face
from tests.constants import source_jpg, target_png, IMAGE_SHAPE, tmp_dir, no_face_jpg

parameters: Namespace = Parameters(f'--execution-provider=cpu --execution-threads={multiprocessing.cpu_count()} --max-memory=12 --source-path="{source_jpg}" --target-path="{target_png}" --output-path="{tmp_dir}"').parameters


def get_test_object() -> FaceSwapper:
    return FaceSwapper(parameters=parameters)


def test_init():
    test_object = get_test_object()
    assert (test_object, FaceSwapper)
    assert (test_object._face_analyser, FaceAnalyser)
    assert (test_object._face_swapper, FaceSwapperType)


def test_face_analysis():
    face = get_test_object().source_face
    assert (face, Face)
    assert face.age == 31
    assert face.sex == 'F'


def test_no_face_found(capsys):
    face = FaceSwapper(parameters=Parameters(f'--source-path="{no_face_jpg}" --target-path="{target_png}" --output-path="{tmp_dir}"').parameters).source_face
    assert face is None
    captured: str = capsys.readouterr()
    captured = captured.out.splitlines()[-1].strip()
    assert captured.find(f'{Fore.BLACK}{Back.RED}FaceSwapper: There is no face found on {no_face_jpg}{Back.RESET}{Fore.RESET}') != -1


def test_process_frame():
    processed_frame = get_test_object().process_frame(CV2VideoHandler.read_image(target_png))
    assert (processed_frame, Frame)
    assert processed_frame.shape == IMAGE_SHAPE
