import os

from sinner.utilities import resolve_relative_path

TARGET_FC = 98
TARGET_FPS = 25.0
FRAME_SHAPE = (360, 640, 3)
IMAGE_SHAPE = (1080, 861, 3)

source_jpg: str = resolve_relative_path('data/sources/source.jpg', __file__)
target_png: str = resolve_relative_path('data/targets/target.png', __file__)
target_mp4: str = resolve_relative_path('data/targets/target.mp4', __file__)
tmp_dir: str = resolve_relative_path('data/temp', __file__)
state_frames_dir: str = resolve_relative_path('data/frames', __file__)
result_mp4: str = os.path.join(tmp_dir, 'result.mp4')
result_png: str = os.path.join(tmp_dir, 'result.png')
