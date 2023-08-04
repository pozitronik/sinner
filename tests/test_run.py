# testing different run configurations
import glob
import multiprocessing
import os.path
import shutil

import pytest

from sinner.Parameters import Parameters
from sinner.Core import Core
from sinner.utilities import limit_resources, suggest_max_memory
from sinner.validators.LoaderException import LoadingException
from tests.constants import target_png, source_jpg, target_mp4, source_target_png_result, source_target_mp4_result, state_frames_dir, result_mp4, tmp_dir, result_png, TARGET_FC, images_dir, source_images_result

threads_count = multiprocessing.cpu_count()


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    if os.path.exists(source_target_png_result):
        os.remove(source_target_png_result)
    if os.path.exists(source_images_result):
        os.remove(source_images_result)
    if os.path.exists(source_target_mp4_result):
        os.remove(source_target_mp4_result)


def setup_function():
    setup()


def test_no_parameters() -> None:
    params = Parameters()
    limit_resources(suggest_max_memory())
    with pytest.raises(LoadingException):
        Core(parameters=params.parameters).run()  # target path is fucked up


def test_no_source() -> None:
    params = Parameters(f'--target_path="{target_png}" --source_path=no_such_file')
    limit_resources(suggest_max_memory())
    with pytest.raises(LoadingException):
        Core(parameters=params.parameters).run()  # source path is fucked up


def test_swap_image() -> None:
    assert os.path.exists(source_target_png_result) is False
    params = Parameters(f'--target-path="{target_png}" --source-path="{source_jpg}"')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    assert os.path.exists(source_target_png_result) is True


def test_swap_mp4() -> None:
    if 'CI' in os.environ:
        pytest.skip("This test is not ready for GitHub CI")
    assert os.path.exists(source_target_mp4_result) is False
    params = Parameters(f'--target-path="{target_mp4}" --source-path="{source_jpg}" --execution-treads={threads_count}')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    assert os.path.exists(source_target_mp4_result) is True


def test_swap_frames_to_mp4() -> None:
    assert os.path.exists(result_mp4) is False
    params = Parameters(f'--target-path="{state_frames_dir}" --source-path="{source_jpg}" --output-path="{result_mp4}" --execution-treads={threads_count}')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    assert os.path.exists(result_mp4) is True


def test_swap_images() -> None:
    assert os.path.exists(source_images_result) is False
    original_images_names = glob.glob(os.path.join(images_dir, '*.jpg'))
    params = Parameters(f'--target-path="{images_dir}" --source-path="{source_jpg}" --execution-treads={threads_count}')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    assert os.path.exists(source_images_result) is True
    result_image_names = glob.glob(os.path.join(source_images_result, '*.*'))
    for name in original_images_names:
        assert name in result_image_names


def test_enhance_image() -> None:
    assert os.path.exists(result_png) is False
    params = Parameters(f'--frame-processor=FaceEnhancer --target-path="{target_png}" --output-path="{result_png}"')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    assert os.path.exists(result_png) is True


def test_swap_enhance_image() -> None:
    assert os.path.exists(result_png) is False
    params = Parameters(f'--frame-processor FaceSwapper FaceEnhancer --source-path="{source_jpg}" --target-path="{target_png}" --output-path="{result_png}" --execution-treads=16')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    assert os.path.exists(result_png) is True


def test_swap_enhance_mp4() -> None:
    if 'CI' in os.environ:
        pytest.skip("This test is not ready for GitHub CI")
    assert os.path.exists(result_mp4) is False
    params = Parameters(f'--frame-processor FaceSwapper FaceEnhancer --source-path="{source_jpg}" --target-path="{target_mp4}" --output-path="{result_mp4}" --execution-treads={threads_count} --keep-frames --temp-dir="{tmp_dir}"')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    assert os.path.exists(result_mp4) is True
    assert os.path.exists(os.path.join(tmp_dir, 'FaceSwapper/target.mp4/source.jpg', '09.png')) is True
    assert os.path.exists(os.path.join(tmp_dir, 'FaceEnhancer/target.mp4/source.jpg', '09.png')) is True


def test_swap_enhance_mp4_extract() -> None:
    if 'CI' in os.environ:
        pytest.skip("This test is not ready for GitHub CI")
    assert os.path.exists(result_mp4) is False
    params = Parameters(f'--frame-processor FaceSwapper FaceEnhancer --source-path="{source_jpg}" --target-path="{target_mp4}" --output-path="{result_mp4}" --extract-frames --execution-treads={threads_count}')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    assert os.path.exists(result_mp4) is True


def test_dummy_mp4_extract_keep_frames() -> None:
    if 'CI' in os.environ:
        pytest.skip("This test is not ready for GitHub CI")
    assert os.path.exists(result_mp4) is False
    params = Parameters(f'--frame-processor DummyProcessor --target-path="{target_mp4}" --output-path="{result_mp4}" --extract-frames --keep-frames --temp-dir="{tmp_dir}"')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    assert os.path.exists(result_mp4) is True
    assert os.path.exists(os.path.join(tmp_dir, 'DummyProcessor', 'target.mp4')) is True
    assert len(glob.glob(os.path.join(tmp_dir, 'DummyProcessor', 'target.mp4', '*.png'))) == TARGET_FC


def test_set_execution_provider(capsys) -> None:
    assert os.path.exists(result_png) is False
    params = Parameters(f'--target-path="{target_png}" --source-path="{source_jpg}" --temp-dir="{tmp_dir}" --output-path="{result_png}" --execution-provider=cpu')
    limit_resources(suggest_max_memory())
    Core(parameters=params.parameters).run()
    captured = capsys.readouterr()
    assert "Error Unknown Provider Type" not in captured.out
    assert os.path.exists(result_png) is True
