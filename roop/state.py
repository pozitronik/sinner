import glob
import os
import shutil
from typing import List
from pathlib import Path

from roop.capturer import get_video_frame_total
from roop.parameters import Parameters
from roop.utilities import get_temp_directory_path, is_video, create_temp

TEMP_DIRECTORY = 'temp'
IN_DIR = 'in'
OUT_DIR = 'out'


class State:
    frames_count: int | None
    in_dir: str
    out_dir: str
    source_path: str
    target_path: str
    output_path: str

    is_multi_frame: bool  # for single frame changes (i.e. picture to picture) the state is always persistent
    preserve_source_frames: bool = True  # keeps extracted source frames for future usage

    def __init__(self, params: Parameters):
        self.source_path = params.source_path
        self.target_path = params.target_path
        self.output_path = params.output_path
        self.in_dir, self.out_dir = self.get_state_dirs()
        self.is_multi_frame = is_video(self.target_path)
        self.frames_count = get_video_frame_total(self.target_path) if self.is_multi_frame else None

    #  creates the state for a provided target
    def create(self):
        Path(self.in_dir).mkdir(parents=True, exist_ok=True)
        Path(self.out_dir).mkdir(parents=True, exist_ok=True)
        if self.is_multi_frame:
            pass
        else:
            shutil.copy(self.target_path, self.in_dir)

    def finish(self):
        if self.is_multi_frame:
            pass
        else:
            shutil.move(self.get_frame_processed_name(self.target_path), self.output_path)

    def get_state_dirs(self) -> tuple[str, str]:
        target_name = os.path.basename(self.target_path)
        source_name = os.path.basename(self.source_path)
        target_directory_path = os.path.dirname(self.target_path)
        in_dir = os.path.join(target_directory_path, TEMP_DIRECTORY, target_name, IN_DIR)
        out_dir = os.path.join(target_directory_path, TEMP_DIRECTORY, target_name, OUT_DIR, source_name)
        return in_dir, out_dir

    #  Checks if all frames in the target file temp folder are processed
    def is_done(self) -> bool:
        return self.is_multi_frame and (self.processed_frames_count() > 0) and (0 == self.unprocessed_frames_count())

    #  Checks if the temp directory with frames is existed and all frames are extracted (or some already processed) for target
    def is_resumable(self) -> bool:
        return self.is_multi_frame and (self.processed_frames_count() > 0) or self.in_frames_count() == self.frames_count

    #  Checks if the temp directory with frames is completely processed (and can be deleted)
    def is_finished(self) -> bool:
        return self.is_multi_frame and self.is_done() and self.processed_frames_count() == self.frames_count

    #  Returns count of already processed frames for this target path (0, if none).
    def processed_frames_count(self) -> int:
        if not self.is_multi_frame: return 0;
        return len([os.path.join(self.out_dir, file) for file in os.listdir(self.out_dir) if file.endswith(".png")])

    #  Returns count of still unprocessed frames for this target path (0, if none).
    def unprocessed_frames_count(self) -> int:
        if not self.is_multi_frame: return 1;
        return self.in_frames_count() - self.processed_frames_count()

    #  returns count of extracted frames in the input dir
    def in_frames_count(self) -> int:
        return len([os.path.join(self.in_dir, file) for file in os.listdir(self.in_dir) if file.endswith(".png")])

    #  Returns a processed file name for an unprocessed frame file name
    def get_frame_processed_name(self, unprocessed_frame_name: str) -> str:
        _, filename = os.path.split(unprocessed_frame_name)
        return str(os.path.join(self.out_dir, filename))

    #  Returns all unprocessed frames
    def unprocessed_frames(self) -> List[str]:
        if not self.is_multi_frame: return [os.path.join(glob.escape(self.out_dir), os.path.basename(self.target_path))]
        processed_frames = self.processed_frames(True)
        return [file for file in glob.glob(os.path.join(glob.escape(self.in_dir), '*.png')) if not (os.path.basename(file) in processed_frames)]

    def processed_frames(self, basename: bool = False) -> List[str]:
        if not self.is_multi_frame: return []
        frame_paths = [file for file in glob.glob(os.path.join(glob.escape(self.out_dir), '*.png'))]
        return [os.path.basename(file) for file in frame_paths] if basename else frame_paths

    def set_processed(self, frame_path):
        if not self.preserve_source_frames: os.remove(frame_path)
