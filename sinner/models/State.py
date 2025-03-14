import os
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List

from sinner.helpers.FrameHelper import write_to_image, EmptyFrame
from sinner.models.NumberedFrame import NumberedFrame
from sinner.models.status.StatusMixin import StatusMixin
from sinner.models.status.Mood import Mood
from sinner.utilities import is_absolute_path, format_sequences, path_exists, is_file, normalize_path, get_file_name
from sinner.validators.AttributeLoader import Rules, AttributeLoader


class State(AttributeLoader, StatusMixin):
    emoji: str = '👀'
    source_path: str | None = None
    initial_target_path: str | None = None

    _target_path: str | None = None
    _path: str | None = None
    frames_count: int
    processor_name: str
    _temp_dir: str
    _zfill_length: int | None

    final_check_state: bool = True
    final_check_empty: bool = True
    final_check_integrity: bool = True

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path',
                'filter': lambda: normalize_path(self.source_path)
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'initial_target_path',  # issue 29: need to know this parameter to avoid names collisions
                'filter': lambda: normalize_path(self.initial_target_path)
            },
            {
                'module_help': 'The state control module'
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
        if not is_absolute_path(value or ''):
            raise Exception("Relative paths is not supported")
        self._temp_dir = os.path.abspath(str(normalize_path(value or '')))

    @property
    def target_path(self) -> str | None:
        return self._target_path

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        self._target_path = os.path.abspath(str(normalize_path(value))) if value is not None else None

    @staticmethod
    def make_path(path: str) -> str:
        if not path_exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

    @property
    def path(self) -> str:
        """
        Processors may not need the source or (in theory) the target. Method tries to configure a part of state path
        for any situation
        :return: adapted state path
        """
        if self._path is None:
            if self.initial_target_path is not None:
                target_path = os.path.basename(self.initial_target_path)
            else:
                target_path = os.path.basename(self.target_path or '')
            sub_path = (self.processor_name, target_path, os.path.basename(self.source_path or ''))
            self._path = os.path.abspath(os.path.join(self.temp_dir, *sub_path))
            self.make_path(self._path)
        return self._path

    @path.setter
    def path(self, path: str) -> None:
        self._path = path
        self.make_path(self._path)

    def save_temp_frame(self, frame: NumberedFrame) -> None:
        if not write_to_image(frame.frame, self.get_frame_processed_name(frame)):
            raise Exception(f"Error saving frame: {self.get_frame_processed_name(frame)}")

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
        png_files = []
        with os.scandir(self.path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith(".png"):
                    png_files.append(entry.path)
        return png_files

    @property
    def processed_frames_indices(self) -> List[int]:
        indices = []
        with os.scandir(self.path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith(".png"):
                    indices.append((int(get_file_name(entry.name))))
        return indices

    #  Returns count of already processed frame for this target (0, if none).
    @property
    def processed_frames_count(self) -> int:
        return len(self.processed_frames)

    #  Returns count of still unprocessed frame for this target (0, if none).
    @property
    def unprocessed_frames_count(self) -> int:
        return self.frames_count - self.processed_frames_count

    #  Returns a processed file name for an unprocessed frame index
    def get_frame_processed_name(self, frame: NumberedFrame) -> str:
        if frame.name:
            filename = frame.name + '.png'
        else:
            filename = str(frame.index).zfill(self.zfill_length) + '.png'
        return str(os.path.join(self.path, filename))

    @property
    def zfill_length(self) -> int:
        if self._zfill_length is None:
            self._zfill_length = len(str(self.frames_count))
        return self._zfill_length

    def final_check(self) -> tuple[bool, List[int]]:
        result = True
        processed_frames_count = self.processed_frames_count
        if self.final_check_state and not self.is_finished:
            self.update_status(message=f"The final processing check failed: processing is done, but state is not finished. Check in {self.path}, may be some frames lost?", mood=Mood.BAD)
            result = False

        if self.final_check_empty:  # check if all frames are non zero-sized
            zero_sized_files_count = 0
            for file_path in self.processed_frames:
                if is_file(file_path) and os.path.getsize(file_path) == 0:
                    zero_sized_files_count += 1
            if zero_sized_files_count > 0:
                self.update_status(message=f"There are zero-sized files in {self.path} temp directory ({zero_sized_files_count} of {processed_frames_count}). Check for free disk space and access rights.", mood=Mood.BAD)
                result = False
        lost_frames = []
        if self.final_check_integrity and not self.is_finished:
            lost_frames = self.check_integrity()
            if lost_frames:
                self.update_status(message=f"There are lost frames in the processed sequence: {format_sequences(lost_frames)}", mood=Mood.BAD)
                result = False

        return result, lost_frames

    def check_integrity(self) -> List[int]:
        result: List[int] = []
        for frame_index in range(self.frames_count):
            f_name = self.get_frame_processed_name(NumberedFrame(frame_index, EmptyFrame))
            if not path_exists(f_name):
                result.append(frame_index)
        return result
