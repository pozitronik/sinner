import os
import shutil
from pathlib import Path

TEMP_DIRECTORY = 'temp'  # todo: make a parameter


class State:
    frames_count: int | None
    out_dir: str
    source_path: str
    target_path: str
    output_path: str

    preserve_source_frames: bool = True  # keeps extracted source frames for future usage

    _zfill_name: int = 4

    def __init__(self, source_path: str, target_path: str, output_path: str, keep_frames: bool = False, frames_count: int | None = None):
        self.source_path = source_path
        self.target_path = target_path
        self.output_path = output_path
        self.keep_frames = keep_frames
        self.out_dir = self.get_out_dir()
        self.frames_count = frames_count
        self._zfill_name = len(str(self.frames_count))
        self.create()

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
