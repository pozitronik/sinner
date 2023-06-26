import os
import shutil
from pathlib import Path

from roop.handlers.frames.CV2VideoHandler import CV2VideoHandler
from roop.parameters import Parameters
from roop.utilities import is_video

TEMP_DIRECTORY = 'temp'  # todo: make a parameter


class State:
    frames_count: int | None
    out_dir: str
    source_path: str
    target_path: str
    output_path: str

    preserve_source_frames: bool = True  # keeps extracted source frames for future usage

    _zfill_name: int = 4

    def __init__(self, params: Parameters):
        self.source_path = params.source_path
        self.target_path = params.target_path
        self.output_path = params.output_path
        self.keep_frames = params.keep_frames
        self.out_dir = self.get_out_dir()
        self.is_multi_frame = is_video(self.target_path)  # todo подумать
        self.frames_count = CV2VideoHandler(self.target_path).fc if self.is_multi_frame else 1
        self._zfill_name = len(str(self.frames_count))

    #  creates the state for a provided target
    def create(self) -> None:
        Path(self.out_dir).mkdir(parents=True, exist_ok=True)

    def finish(self) -> None:
        if self.keep_frames is False:
            shutil.rmtree(self.out_dir)

    def get_out_dir(self) -> str:
        return os.path.join(os.path.dirname(self.target_path), TEMP_DIRECTORY, os.path.basename(self.target_path), os.path.basename(self.source_path))

    #  Checks if some frames already processed
    def is_started(self) -> bool:
        return self.frames_count > self.processed_frames_count() > 0

    #  Checks if the process is finished
    def is_finished(self) -> bool:
        return self.frames_count == self.processed_frames_count()

    #  Returns count of already processed frames for this target  (0, if none).
    def processed_frames_count(self) -> int:
        return len([os.path.join(self.out_dir, file) for file in os.listdir(self.out_dir) if file.endswith(".png")])

    #  Returns count of still unprocessed frames for this target (0, if none).
    def unprocessed_frames_count(self) -> int:
        return self.frames_count - self.processed_frames_count()

    #  Returns a processed file name for an unprocessed frame index
    def get_frame_processed_name(self, frame_index: int) -> str:
        filename = str(frame_index + 1).zfill(self._zfill_name) + '.png'
        return str(os.path.join(self.out_dir, filename))
