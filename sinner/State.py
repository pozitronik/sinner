import os
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List

from sinner.Status import Status, Mood
from sinner.typing import Frame
from sinner.utilities import write_image
from sinner.validators.AttributeLoader import AttributeLoader, Rules

OUT_DIR = 'OUT'
IN_DIR = 'IN'


class State(AttributeLoader, Status):
    source_path: str | None = None
    initial_target_path: str | None = None

    _target_path: str | None = None
    frames_count: int
    processor_name: str
    _temp_dir: str
    _zfill_length: int | None
    _in_dir: str | None = None
    _out_dir: str | None = None

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path'
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'initial_target_path'  # issue 29: need to know this parameter to avoid names collisions
            }
        ]

    def __init__(self, parameters: Namespace, target_path: str | None, temp_dir: str, frames_count: int, processor_name: str):
        super().__init__(parameters)
        self.target_path = target_path
        self.temp_dir = temp_dir
        self.frames_count = frames_count
        self.processor_name = processor_name
        self._zfill_length = None
        state: List[Dict[str, Any]] = [
            {"Source": getattr(self, "source_path", "None")},
            {"Target": self.target_path},
            {"Temporary dir": self.temp_dir}
        ]
        state_string = "\n".join([f"\t{key}: {value}" for dict_line in state for key, value in dict_line.items()])
        self.update_status(f'The processing state:\n{state_string}')

    @property
    def temp_dir(self) -> str:
        return self._temp_dir

    @temp_dir.setter
    def temp_dir(self, value: str | None) -> None:
        if not os.path.isabs(value or ''):
            raise Exception("Relative paths is not supported")
        self._temp_dir = os.path.abspath(os.path.normpath(value or ''))

    @property
    def target_path(self) -> str | None:
        return self._target_path

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        self._target_path = os.path.abspath(os.path.normpath(value)) if value is not None else None

    @property
    def out_dir(self) -> str:
        if self._out_dir is None:
            self._out_dir = os.path.abspath(os.path.normpath(self.make_path(self.state_path(OUT_DIR))))
            self.update_status(f'The output directory is {self._out_dir}')
        return self._out_dir

    @out_dir.setter
    def out_dir(self, value: str) -> None:
        self._out_dir = os.path.abspath(os.path.normpath(value))
        self.update_status(f'The output directory is changed to {self._out_dir}')

    @property
    def in_dir(self) -> str:
        if self._in_dir is None:
            self._in_dir = os.path.abspath(os.path.normpath(self.make_path(self.state_path(IN_DIR))))
            self.update_status(f'The input directory is {self._in_dir}')
        return self._in_dir

    @in_dir.setter
    def in_dir(self, value: str) -> None:
        self._in_dir = os.path.abspath(os.path.normpath(value))
        self.update_status(f'The input directory is changed to {self._in_dir}')

    @staticmethod
    def make_path(path: str) -> str:
        if not os.path.exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def state_path(self, dir_type: str) -> str:
        """
        Processors may not need the source or (in theory) the target. Method tries to configure a part of state path
        for any situation
        :return: adapted state path
        """
        if self.initial_target_path is not None:
            target_path = os.path.basename(self.initial_target_path)
        else:
            target_path = os.path.basename(self.target_path or '')
        sub_path = (self.processor_name, target_path, os.path.basename(self.source_path or ''), dir_type)
        return os.path.join(self.temp_dir, *sub_path)

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
        return self.frames_count <= self.processed_frames_count != 0

    @property
    def processed_frames(self) -> List[str]:
        return [os.path.join(self.out_dir, file) for file in os.listdir(self.out_dir) if file.endswith(".png")]

    #  Returns count of already processed frame for this target (0, if none).
    @property
    def processed_frames_count(self) -> int:
        return len(self.processed_frames)

    @property
    def extracted_frames(self) -> List[str]:
        return [os.path.join(self.in_dir, file) for file in os.listdir(self.in_dir) if file.endswith(".png")]

    #  Returns count of already extracted frame for this target (0, if none).
    @property
    def extracted_frames_count(self) -> int:
        return len(self.extracted_frames)

    #  Returns count of still unprocessed frame for this target (0, if none).
    @property
    def unprocessed_frames_count(self) -> int:
        return self.frames_count - self.processed_frames_count

    #  Returns a processed file name for an unprocessed frame index
    def get_frame_processed_name(self, frame_index: int) -> str:
        filename = str(frame_index).zfill(self.zfill_length) + '.png'
        return str(os.path.join(self.out_dir, filename))

    @property
    def zfill_length(self) -> int:
        if self._zfill_length is None:
            self._zfill_length = len(str(self.frames_count))
        return self._zfill_length

    def final_check(self) -> bool:
        result = True
        processed_frames_count = self.processed_frames_count
        if not self.is_finished:
            self.update_status(message=f"The final processing check failed: processing is done, but state is not finished. Check in {self.out_dir}, may be some frames lost?", mood=Mood.BAD)
            result = False

        #  check if the last file name in the processed sequence is right
        last_file_name = int(max(os.scandir(self.out_dir), key=lambda entry: int(os.path.splitext(entry.name)[0])).name.split('.')[0])
        if self.frames_count != last_file_name:
            self.update_status(message=f"Last processed frame is {last_file_name}, but expected {self.frames_count}. Check in {self.out_dir} for it.", mood=Mood.BAD)
            result = False
        #  check if all frames are non zero-sized
        zero_sized_files_count = 0
        for file_path in self.processed_frames:
            if os.path.getsize(file_path) == 0:
                zero_sized_files_count += 1
        if zero_sized_files_count > 0:
            self.update_status(message=f"There is zero-sized files in {self.out_dir} temp directory ({zero_sized_files_count} of {processed_frames_count}). Check for free disk space and access rights.", mood=Mood.BAD)
            result = False
        return result
