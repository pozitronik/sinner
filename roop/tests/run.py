from roop.core import Core
from roop.parameters import Parameters
from roop.state import State
from roop.utilities import limit_resources, get_video_handler, get_frame_processor


def test_image_to_video_ffmpeg():
    params = Parameters()
    state = State(params)
    state.create()
    limit_resources(params.max_memory)
    core = Core(params=params, state=state, video_handler=get_video_handler(params.target_path, params.video_handler), frame_processor=get_frame_processor(state))
    core.run()

def test_image_to_video_cv2():
    pass

def test_image_to_image():
    pass