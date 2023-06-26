import os
import shutil
from argparse import Namespace

from roop.core import Core
from roop.parameters import Parameters
from roop.state import State
from roop.prototypes import get_video_handler, get_frame_processor
from roop.utilities import limit_resources, resolve_relative_path, is_video

source_jpg: str = resolve_relative_path('data/sources/source.jpg', __file__)
target_mp4: str = resolve_relative_path('data/targets/target.mp4', __file__)
target_png: str = resolve_relative_path('data/targets/target.png', __file__)
result_jpg: str = resolve_relative_path('data/results/result.jpg', __file__)
result_mp4: str = resolve_relative_path('data/results/result.mp4', __file__)
results_dir: str = resolve_relative_path('data/results/', __file__)


def setup():
    #  clean previous results, if exists
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
        keep_frames=False,
        frame_processor='FaceSwapper',
        video_handler='ffmpeg',
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_mp4,
        output_path=result_mp4,
    ))
    state = State(params)
    state.create()
    limit_resources(params.max_memory)
    core = Core(params=params, state=state, video_handler=get_video_handler(params.target_path, params.video_handler), frame_processor=get_frame_processor(params, state))
    core.run()

    frames_count = len([file for file in os.listdir(resolve_relative_path('data/targets/temp/target.mp4/out/source.jpg', __file__))])
    assert frames_count == 62
    assert is_video(result_mp4)
    test_video_handler = get_video_handler(result_mp4, params.video_handler)
    assert test_video_handler.fc == 62
    assert test_video_handler.fps == 30


def test_image_to_video_cv2():
    params = Parameters(Namespace(
        max_memory=4,
        execution_provider='cuda',
        execution_threads=4,
        keep_audio=True,
        keep_frames=False,
        frame_processor='FaceSwapper',
        video_handler='cv2',
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_mp4,
        output_path=result_mp4,
    ))
    state = State(params)
    state.create()
    limit_resources(params.max_memory)
    core = Core(params=params, state=state, video_handler=get_video_handler(params.target_path, params.video_handler), frame_processor=get_frame_processor(params, state))
    core.run()

    frames_count = len([file for file in os.listdir(resolve_relative_path('data/targets/temp/target.mp4/out/source.jpg', __file__))])
    assert frames_count == 62
    assert is_video(result_mp4)
    test_video_handler = get_video_handler(result_mp4, params.video_handler)
    assert test_video_handler.fc == 62
    assert test_video_handler.fps == 30


def test_image_to_image():
    assert os.path.exists(result_jpg) is False
    params = Parameters(Namespace(
        max_memory=4,
        execution_provider='cuda',
        execution_threads=4,
        keep_audio=True,
        keep_frames=False,
        frame_processor='FaceSwapper',
        video_handler=None,  # not required in img-to-img swap
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_png,
        output_path=result_jpg,
    ))
    state = State(params)
    state.create()
    limit_resources(params.max_memory)
    core = Core(params=params, state=state, frame_processor=get_frame_processor(params, state))
    core.run()

    assert os.path.exists(result_jpg) is True
