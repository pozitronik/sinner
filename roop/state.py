import glob
import os
from typing import List

from roop.capturer import get_video_frame_total
from roop.parameters import Parameters
from roop.utilities import get_temp_directory_path, is_video


class State:
    PROCESSED_PREFIX = '_'

    target_path: str
    state_directory: str
    is_multi_frame: bool  # for single frame changes (i.e. picture to picture) the state is always persistent
    preserve_source_frames: bool = True #  keeps extracted source frames for future usage

    def __init__(self, params: Parameters):
        self.target_path = params.target_path
        self.state_directory = get_temp_directory_path(self.target_path)
        self.is_multi_frame = is_video(self.target_path)

    #  Checks if all frames in the target file temp folder are processed
    def is_done(self) -> bool:
        return self.is_multi_frame and (self.processed_frames_count() > 0) and (0 == self.unprocessed_frames_count())

    #  Checks if the temp directory with frames is existed and all frames are extracted (or some already processed) for target
    def is_resumable(self) -> bool:
        return self.is_multi_frame and (self.processed_frames_count() > 0) or self.unprocessed_frames_count() == get_video_frame_total(self.target_path)

    #  Checks if the temp directory with frames is completely processed (and can be deleted)
    def is_finished(self) -> bool:
        return self.is_multi_frame and self.is_done() and self.processed_frames_count() == get_video_frame_total(self.target_path)

    #  Returns count of already processed frames for this target path (0, if none). Once called, stores value in state.processed_frames_cnt global variable
    def processed_frames_count(self) -> int:
        if not os.path.exists(self.state_directory) or not self.is_multi_frame: return 0;
        return len([os.path.join(self.state_directory, file) for file in os.listdir(self.state_directory) if file.startswith(self.PROCESSED_PREFIX) and file.endswith(".png")])

    #  Returns count of still unprocessed frames for this target path (0, if none).
    def unprocessed_frames_count(self) -> int:
        if not os.path.exists(self.state_directory): return 0
        if not self.is_multi_frame: return 1;
        return len([os.path.join(self.state_directory, file) for file in os.listdir(self.state_directory) if self.PROCESSED_PREFIX not in file and file.endswith(".png")])

    #  Returns count all frames for this target path, processed and unprocessed (0, if none).
    def total_frames_count(self) -> int:
        if not os.path.exists(not os.path.exists(self.state_directory)): return 0
        if not self.is_multi_frame: return 1;
        return len([os.path.join(self.state_directory, file) for file in os.listdir(self.state_directory) if file.endswith(".png")])

    #  Returns a processed file name for an unprocessed frame file name
    def get_frame_processed_name(self, unprocessed_frame_name: str) -> str:
        directory, filename = os.path.split(unprocessed_frame_name)
        return str(os.path.join(directory, self.PROCESSED_PREFIX + filename))

    #  Returns all unprocessed frames
    def unprocessed_frames(self) -> List[str]:
        if not self.is_multi_frame:
            return [os.path.join(glob.escape(self.state_directory), os.path.basename(self.target_path))]
        return [file for file in glob.glob(os.path.join(glob.escape(self.state_directory), '*.png')) if not os.path.basename(file).startswith(self.PROCESSED_PREFIX)]

    def set_processed(self, frame_path):
        if not self.preserve_source_frames: os.remove(frame_path)
