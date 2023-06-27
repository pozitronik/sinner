import os
import shutil
from pathlib import Path

from roop.typing import Frame
from roop.utilities import write_image

TEMP_DIRECTORY = 'temp'  # todo: make a parameter


class State:
    frames_count: int
    out_dir: str
    source_path: str
    target_path: str
    output_path: str
    processor_name: str = ''

    preserve_source_frames: bool = True  # keeps extracted source frames for future usage

    _zfill_length: int | None

    def __init__(self, source_path: str, target_path: str, output_path: str, keep_frames: bool = False):
        self.source_path = source_path
        self.target_path = target_path
        self.output_path = output_path
        self.keep_frames = keep_frames
        self._zfill_length = None

    def reload(self) -> None:
        self.target_path = self.out_dir

    def finish(self) -> None:
        if self.keep_frames is False:
            shutil.rmtree(self.out_dir)

    @property
    def out_dir(self) -> str:
        path = os.path.join(os.path.dirname(self.target_path), TEMP_DIRECTORY, self.processor_name, os.path.basename(self.target_path), os.path.basename(self.source_path))
        if not os.path.exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def save_temp_frame(self, frame: Frame, index: int):
        write_image(frame, self.get_frame_processed_name(index))

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
        filename = str(frame_index + 1).zfill(self.get_zfill_length()) + '.png'
        return str(os.path.join(self.out_dir, filename))

    def get_zfill_length(self) -> int:
        if self._zfill_length is None:
            self._zfill_length = len(str(self.frames_count))
        return self._zfill_length
