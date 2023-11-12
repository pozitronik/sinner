import os

from sinner.utilities import resolve_relative_path, get_app_dir

TARGET_FC = 10
TARGET_FPS = 10.0
TARGET_RESOLUTION = (640, 360)
FRAME_SHAPE = (360, 640, 3)
IMAGE_SHAPE = (1080, 861, 3)

# test paths

data_targets_dir: str = resolve_relative_path('data/targets', __file__)
source_jpg: str = resolve_relative_path('data/sources/source.jpg', __file__)
no_face_jpg: str = resolve_relative_path('data/sources/no_face.jpg', __file__)
target_faces: str = os.path.join(data_targets_dir, 'faces.jpg')
target_png: str = os.path.join(data_targets_dir, 'target.png')
target_mp4: str = os.path.join(data_targets_dir, 'target.mp4')
source_target_png: str = os.path.join(data_targets_dir, 'source-target.png')  # auto result name for image swap
result_target_png: str = os.path.join(data_targets_dir, 'result-target.png')  # auto result name for image processing
source_target_mp4: str = os.path.join(data_targets_dir, 'source-target.mp4')  # auto result name for video swap
result_target_mp4: str = os.path.join(data_targets_dir, 'result-target.mp4')  # auto result name for video processing
source_images_result: str = resolve_relative_path('data/source-images', __file__)  # auto result name for images swap
result_frames: str = resolve_relative_path('data/result-frames', __file__)  # auto result name for frames processing
source_frames: str = resolve_relative_path('data/source-frames', __file__)  # auto result name for frames swap
tmp_dir: str = resolve_relative_path('temp', get_app_dir())

state_frames_dir: str = resolve_relative_path('data/frames', __file__)
images_dir: str = resolve_relative_path('data/images', __file__)
result_mp4: str = os.path.join(tmp_dir, 'result.mp4')
result_png: str = os.path.join(tmp_dir, 'result.png')

test_config: str = resolve_relative_path('data/test.ini', __file__)
test_config_bak: str = resolve_relative_path('data/test.ini.bak', __file__)
test_logfile: str = resolve_relative_path('data/test.log', __file__)
