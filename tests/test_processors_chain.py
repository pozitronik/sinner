import os
import shutil
from argparse import Namespace

from roop.core import Core
from roop.handlers.frame.BaseFrameHandler import BaseFrameHandler
from roop.parameters import Parameters
from roop.utilities import resolve_relative_path, limit_resources, is_video

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


def test_chain():
    params = Parameters(Namespace(
        max_memory=4,
        execution_provider='cuda',
        execution_threads=4,
        keep_audio=True,
        keep_frames=True,
        in_memory=False,
        temp_dir=tmp_dir,
        frame_processor=['FaceSwapper', 'DummyProcessor'],
        frame_handler=None,
        fps=None,
        many_faces=False,
        source_path=source_jpg,
        target_path=target_mp4,
        output_path=result_mp4,
    ))
    limit_resources(params.max_memory)
    core = Core(params=params)
    core.run()

    assert 62 == len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/IN', __file__))])
    assert 62 == len([file for file in os.listdir(resolve_relative_path('data/temp/FaceSwapper/target.mp4/source.jpg/OUT', __file__))])
    assert 62 == len([file for file in os.listdir(resolve_relative_path('data/temp/DummyProcessor/OUT/source.jpg/OUT', __file__))])
    assert False == os.path.exists(resolve_relative_path('data/temp/DummyProcessor/OUT/source.jpg/IN ', __file__))
    assert is_video(result_mp4)
    test_video_handler = BaseFrameHandler.create(handler_name=params.frame_handler, target_path=result_mp4)
    assert test_video_handler.fc == 62
    assert test_video_handler.fps == 30
