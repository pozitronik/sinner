import os

from sinner.utilities import resolve_relative_path, get_app_dir

TARGET_FC = 10
TARGET_FPS = 10.0
FRAME_SHAPE = (360, 640, 3)
IMAGE_SHAPE = (1080, 861, 3)

source_jpg: str = resolve_relative_path('data/sources/source.jpg', __file__)
target_faces: str = resolve_relative_path('data/targets/faces.jpg', __file__)
target_png: str = resolve_relative_path('data/targets/target.png', __file__)
target_mp4: str = resolve_relative_path('data/targets/target.mp4', __file__)
source_target_png_result: str = resolve_relative_path('data/targets/source-target.png', __file__)  # auto result name for image swap
source_target_mp4_result: str = resolve_relative_path('data/targets/source-target.mp4', __file__)  # auto result name for video swap
tmp_dir: str = resolve_relative_path('temp', get_app_dir())
state_frames_dir: str = resolve_relative_path('data/frames', __file__)
result_mp4: str = os.path.join(tmp_dir, 'result.mp4')
result_png: str = os.path.join(tmp_dir, 'result.png')

test_config: str = resolve_relative_path('data/test.ini', __file__)
test_logfile: str = resolve_relative_path('data/test.log', __file__)
