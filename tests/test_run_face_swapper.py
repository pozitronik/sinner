import os
import shutil
from argparse import Namespace
from pathlib import Path

from roop.core import Core
from roop.handlers.frame.BaseFrameHandler import BaseFrameHandler
from roop.parameters import Parameters
from roop.utilities import limit_resources, resolve_relative_path, is_video

source_jpg: str = resolve_relative_path('data/sources/source.jpg', __file__)
target_mp4: str = resolve_relative_path('data/targets/target.mp4', __file__)
target_png: str = resolve_relative_path('data/targets/target.png', __file__)
result_jpg: str = resolve_relative_path('data/results/result.jpg', __file__)
result_mp4: str = resolve_relative_path('data/results/result.mp4', __file__)
results_dir: str = resolve_relative_path('data/results/', __file__)
tmp_dir: str = resolve_relative_path('data/temp', __file__)
state_frames_dir: str = resolve_relative_path('data/frames', __file__)


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    if os.path.exists(results_dir):
        shutil.rmtree(results_dir)
    if not os.path.exists(results_dir):
        os.mkdir(results_dir, 0o777)


def setup_function(function):
    setup()


def test_image_to_video_ffmpeg():
    params = Parameters(Namespace(
        max_memory=4,
        execution_provider='cuda',
        execution_threads=4,
        keep_audio=True,
        keep_frames=True,
        in_memory=False,
        temp_dir=tmp_dir,
        frame_processor=['FaceSwapper'],
        frame_handler='FFmpegVideoHandler',
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_mp4,
        output_path=result_mp4,
    ))
    limit_resources(params.max_memory)
    core = Core(params=params)
    core.run()

    extracted_frames_count = len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/IN', __file__))])
    assert extracted_frames_count == 62
    swapped_frames_count = len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/OUT', __file__))])
    assert swapped_frames_count == 62
    assert is_video(result_mp4)
    test_video_handler = BaseFrameHandler.create(handler_name=params.frame_handler, target_path=result_mp4)
    assert test_video_handler.fc == 62
    assert test_video_handler.fps == 30


# test processing continuation
def test_image_to_video_ffmpeg_continue():
    params = Parameters(Namespace(
        max_memory=4,
        execution_provider='cuda',
        execution_threads=4,
        keep_audio=True,
        keep_frames=True,
        in_memory=False,
        temp_dir=tmp_dir,
        frame_processor=['FaceSwapper'],
        frame_handler='FFmpegVideoHandler',
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_mp4,
        output_path=result_mp4,
    ))

    limit_resources(params.max_memory)
    core = Core(params=params)

    out_dir = resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/OUT', __file__)

    assert os.path.exists(out_dir) is False  # check if out directory is empty
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for filename in [f'{"%02d" % i}.png' for i in range(1, 31)]:  # copy files from 0001.png to 0030.png to out dir
        shutil.copy(os.path.join(state_frames_dir, filename), os.path.join(out_dir, filename))
    assert 30 == len(os.listdir(out_dir))
    core.run()

    extracted_frames_count = len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/IN', __file__))])
    assert extracted_frames_count == 32
    swapped_frames_count = len([file for file in os.listdir(out_dir)])
    assert swapped_frames_count == 62
    assert is_video(result_mp4)
    test_video_handler = BaseFrameHandler.create(handler_name=params.frame_handler, target_path=result_mp4)
    assert test_video_handler.fc == 62
    assert test_video_handler.fps == 30


def test_image_to_video_cv2():
    params = Parameters(Namespace(
        max_memory=4,
        execution_provider='cuda',
        execution_threads=4,
        keep_audio=True,
        keep_frames=True,
        in_memory=False,
        temp_dir=tmp_dir,
        frame_processor=['FaceSwapper'],
        frame_handler='CV2VideoHandler',
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_mp4,
        output_path=result_mp4,
    ))
    limit_resources(params.max_memory)
    core = Core(params=params)
    core.run()

    extracted_frames_count = len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/IN', __file__))])
    assert extracted_frames_count == 62
    swapped_frames_count = len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/OUT', __file__))])
    assert swapped_frames_count == 62
    assert is_video(result_mp4)
    test_video_handler = BaseFrameHandler.create(handler_name=params.frame_handler, target_path=result_mp4)
    assert test_video_handler.fc == 62
    assert test_video_handler.fps == 30


def test_image_to_video_cv2_continue():
    params = Parameters(Namespace(
        max_memory=4,
        execution_provider='cuda',
        execution_threads=4,
        keep_audio=True,
        keep_frames=True,
        in_memory=False,
        temp_dir=tmp_dir,
        frame_processor=['FaceSwapper'],
        frame_handler='CV2VideoHandler',
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_mp4,
        output_path=result_mp4,
    ))

    limit_resources(params.max_memory)
    core = Core(params=params)

    out_dir = resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/OUT', __file__)

    assert os.path.exists(out_dir) is False  # check if out directory is empty
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for filename in [f'{"%02d" % i}.png' for i in range(1, 32)]:  # copy files from 0001.png to 0030.png to out dir
        shutil.copy(os.path.join(state_frames_dir, filename), os.path.join(out_dir, filename))
    assert 31 == len(os.listdir(out_dir))
    core.run()

    extracted_frames_count = len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/IN', __file__))])
    assert extracted_frames_count == 31
    swapped_frames_count = len([file for file in os.listdir(out_dir)])
    assert swapped_frames_count == 62
    assert is_video(result_mp4)
    test_video_handler = BaseFrameHandler.create(handler_name=params.frame_handler, target_path=result_mp4)
    assert test_video_handler.fc == 62
    assert test_video_handler.fps == 30


def test_image_to_image():
    assert os.path.exists(result_jpg) is False
    params = Parameters(Namespace(
        max_memory=4,
        execution_provider='cuda',
        execution_threads=4,
        keep_audio=True,
        keep_frames=True,
        in_memory=False,
        temp_dir=tmp_dir,
        frame_processor=['FaceSwapper'],
        frame_handler=None,  # will be auto suggested
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_png,
        output_path=result_jpg,
    ))
    limit_resources(params.max_memory)
    core = Core(params=params)
    core.run()

    assert os.path.exists(result_jpg) is True


def test_image_to_video_ffmpeg_multi_provider():
    params = Parameters(Namespace(
        max_memory=4,
        execution_provider='cuda' + 'cpu',
        execution_threads=4,
        keep_audio=True,
        keep_frames=True,
        in_memory=False,
        temp_dir=tmp_dir,
        frame_processor=['FaceSwapper'],
        frame_handler='FFmpegVideoHandler',
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_mp4,
        output_path=result_mp4,
    ))
    limit_resources(params.max_memory)
    core = Core(params=params)
    core.run()

    extracted_frames_count = len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/IN', __file__))])
    assert extracted_frames_count == 62
    swapped_frames_count = len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/OUT', __file__))])
    assert swapped_frames_count == 62
    assert is_video(result_mp4)
    test_video_handler = BaseFrameHandler.create(handler_name=params.frame_handler, target_path=result_mp4)
    assert test_video_handler.fc == 62
    assert test_video_handler.fps == 30
