import os
from argparse import Namespace

from roop.core import Core
from roop.parameters import Parameters
from roop.state import State
from roop.tests.prototypes import get_video_handler, get_frame_processor
from roop.utilities import limit_resources, resolve_relative_path, is_video


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
        source_path=resolve_relative_path('data\\sources\\source.jpg', __file__),
        target_path=resolve_relative_path('data\\targets\\target.mp4', __file__),
        output_path=resolve_relative_path('data\\results\\result.mp4', __file__),
    ))
    state = State(params)
    state.create()
    limit_resources(params.max_memory)
    core = Core(params=params, state=state, video_handler=get_video_handler(params.target_path, params.video_handler), frame_processor=get_frame_processor(params, state))
    core.run()

    frames_count = len([file for file in os.listdir(resolve_relative_path('data\\targets\\temp\\target.mp4\\out\\source.jpg', __file__))])
    assert frames_count == 450
    assert is_video(resolve_relative_path('data\\results\\result.mp4', __file__))


def test_image_to_video_cv2():
    pass


def test_image_to_image():
    pass
