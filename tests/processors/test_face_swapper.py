import multiprocessing

import numpy as np
import pytest
from colorama import Fore, Back
from insightface.app.common import Face

from sinner.Parameters import Parameters
from sinner.FaceAnalyser import FaceAnalyser
from sinner.helpers.FrameHelper import read_from_image
from sinner.processors.frame.FaceSwapper import FaceSwapper
from sinner.typing import Frame, FaceSwapperType
from tests.constants import source_jpg, target_png, IMAGE_SHAPE, tmp_dir, no_face_jpg, male_face_jpg, female_face_jpg, multiple_faces_jpg


def get_test_object(additional_params: str = "") -> FaceSwapper:
    params = f'--execution-provider=cpu --execution-threads={multiprocessing.cpu_count()} --max-memory=12 --source-path="{source_jpg}" --target-path="{target_png}" --output-path="{tmp_dir}" {additional_params}'
    return FaceSwapper(parameters=Parameters(params).parameters)


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
    processed_frame = get_test_object().process_frame(read_from_image(target_png))
    assert (processed_frame, Frame)
    assert processed_frame.shape == IMAGE_SHAPE


@pytest.mark.parametrize("target_gender, source_image, target_image, should_swap", [
    ("M", male_face_jpg, male_face_jpg, True),
    ("M", male_face_jpg, female_face_jpg, False),
    ("F", female_face_jpg, female_face_jpg, True),
    ("F", female_face_jpg, male_face_jpg, False),
    ("B", male_face_jpg, female_face_jpg, True),
    ("B", female_face_jpg, male_face_jpg, True),
    ("I", male_face_jpg, male_face_jpg, True),
    ("I", male_face_jpg, female_face_jpg, False),
    ("I", female_face_jpg, female_face_jpg, True),
    ("I", female_face_jpg, male_face_jpg, False),
])
def test_gender_selection(target_gender, source_image, target_image, should_swap):
    test_object = get_test_object(f'--target-gender={target_gender} --source-path="{source_image}"')
    target_frame = read_from_image(target_image)
    processed_frame = test_object.process_frame(target_frame)

    # Анализируем лица на обработанном кадре
    original_face = test_object.face_analyser.get_one_face(target_frame)
    processed_face = test_object.face_analyser.get_one_face(processed_frame)

    if should_swap:
        if source_image != target_image:
            # Проверяем, что лицо изменилось
            assert not np.allclose(original_face.embedding, processed_face.embedding, atol=1e-5)
        # Проверяем, что пол лица соответствует ожидаемому
        if target_gender in ['M', 'F']:
            assert processed_face.sex == target_gender
        elif target_gender == 'I':
            source_face = test_object.source_face
            assert processed_face.sex == source_face.sex
    else:
        # Проверяем, что лицо не изменилось
        assert np.allclose(original_face.embedding, processed_face.embedding, atol=1e-5)
        assert original_face.sex == processed_face.sex


# test is skipped, because I cant find a good image for it
# def test_unknown_gender_warning(capsys):
#     test_object = get_test_object(f'--target-gender=M --source-path="{unknown_gender_face_jpg}"')
#     target_frame = read_from_image(target_png)
#     _ = test_object.process_frame(target_frame)
#     captured = capsys.readouterr()
#     assert "Unable to determine gender for a face. Skipping this face." in captured.out


def test_many_faces_processing():
    test_object = get_test_object("--many-faces")
    assert test_object.many_faces is True
    target_frame = read_from_image(multiple_faces_jpg)
    processed_frame = test_object.process_frame(target_frame)
    assert not np.array_equal(target_frame, processed_frame)
