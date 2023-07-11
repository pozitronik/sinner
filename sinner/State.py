import os
from argparse import Namespace
from pathlib import Path

from sinner.typing import Frame
from sinner.utilities import write_image
from sinner.validators.AttributeLoader import AttributeLoader, Rules
from sinner.validators.LoaderException import LoadingException

OUT_DIR = 'OUT'
IN_DIR = 'IN'


class State(AttributeLoader):
    frames_count: int
    source_path: str
    target_path: str
    processor_name: str = ''
    temp_dir: str

    _zfill_length: int | None

    def rules(self) -> Rules:
        return super().rules() + [
            {'parameter': 'source_path'},
            {'parameter': 'target_path', 'required': True},
            {'parameter': 'output_path'},
            {'parameter': 'temp_dir', 'required': True},
        ]

    def __init__(self, parameters: Namespace, frames_count: int):
        if not self.load(parameters):
            raise LoadingException(self.errors)
        self.frames_count = frames_count
        self._zfill_length = None

    @property
    def out_dir(self) -> str:
        sub_path = (self.processor_name, os.path.basename(self.target_path), os.path.basename(self.source_path), OUT_DIR)
        path = os.path.join(self.temp_dir, *sub_path)
        if not os.path.exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

    @property
    def in_dir(self) -> str:
        sub_path = (self.processor_name, os.path.basename(self.target_path), os.path.basename(self.source_path), IN_DIR)
        path = os.path.join(self.temp_dir, *sub_path)
        if not os.path.exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def save_temp_frame(self, frame: Frame, index: int) -> None:
        if not write_image(frame, self.get_frame_processed_name(index)):
            raise Exception(f"Error saving frame: {self.get_frame_processed_name(index)}")

    #  Checks if some frame already processed
    @property
    def is_started(self) -> bool:
        return self.frames_count > self.processed_frames_count > 0

    #  Checks if the process is finished
    @property
    def is_finished(self) -> bool:
        return self.frames_count == self.processed_frames_count

    #  Returns count of already processed frame for this target (0, if none).
    @property
    def processed_frames_count(self) -> int:
        return len([os.path.join(self.out_dir, file) for file in os.listdir(self.out_dir) if file.endswith(".png")])

    #  Returns count of already extracted frame for this target (0, if none).
    @property
    def extracted_frames_count(self) -> int:
        return len([os.path.join(self.in_dir, file) for file in os.listdir(self.out_dir) if file.endswith(".png")])

    #  Returns count of still unprocessed frame for this target (0, if none).
    @property
    def unprocessed_frames_count(self) -> int:
        return self.frames_count - self.processed_frames_count

    #  Returns a processed file name for an unprocessed frame index
    def get_frame_processed_name(self, frame_index: int) -> str:
        filename = str(frame_index).zfill(self.get_zfill_length) + '.png'
        return str(os.path.join(self.out_dir, filename))

    @property
    def get_zfill_length(self) -> int:
        if self._zfill_length is None:
            self._zfill_length = len(str(self.frames_count))
        return self._zfill_length
