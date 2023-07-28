import os
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List

from sinner.Status import Status, Mood
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.typing import Frame
from sinner.utilities import is_absolute_path
from sinner.validators.AttributeLoader import AttributeLoader, Rules


class State(AttributeLoader, Status):
    source_path: str | None = None
    initial_target_path: str | None = None

    _target_path: str | None = None
    frames_count: int
    processor_name: str
    _temp_dir: str
    _zfill_length: int | None

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
        if not is_absolute_path(value or ''):
            raise Exception("Relative paths is not supported")
        self._temp_dir = os.path.abspath(os.path.normpath(value or ''))

    @property
    def target_path(self) -> str | None:
        return self._target_path

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        self._target_path = os.path.abspath(os.path.normpath(value)) if value is not None else None

    @staticmethod
    def make_path(path: str) -> str:
        if not os.path.exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

    @property
    def path(self) -> str:
        """
        Processors may not need the source or (in theory) the target. Method tries to configure a part of state path
        for any situation
        :return: adapted state path
        """
        if self.initial_target_path is not None:
            target_path = os.path.basename(self.initial_target_path)
        else:
            target_path = os.path.basename(self.target_path or '')
        sub_path = (self.processor_name, target_path, os.path.basename(self.source_path or ''))
        return os.path.join(self.temp_dir, *sub_path)

    def save_temp_frame(self, frame: Frame, index: int) -> None:
        if not CV2VideoHandler.write_image(frame, self.get_frame_processed_name(index)):
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
        return [os.path.join(self.path, file) for file in os.listdir(self.path) if file.endswith(".png")]

    #  Returns count of already processed frame for this target (0, if none).
    @property
    def processed_frames_count(self) -> int:
        return len(self.processed_frames)

    #  Returns count of still unprocessed frame for this target (0, if none).
    @property
    def unprocessed_frames_count(self) -> int:
        return self.frames_count - self.processed_frames_count

    #  Returns a processed file name for an unprocessed frame index
    def get_frame_processed_name(self, frame_index: int) -> str:
        filename = str(frame_index).zfill(self.zfill_length) + '.png'
        return str(os.path.join(self.path, filename))

    @property
    def zfill_length(self) -> int:
        if self._zfill_length is None:
            self._zfill_length = len(str(self.frames_count))
        return self._zfill_length

    def final_check(self) -> bool:
        result = True
        processed_frames_count = self.processed_frames_count
        if not self.is_finished:
            self.update_status(message=f"The final processing check failed: processing is done, but state is not finished. Check in {self.path}, may be some frames lost?", mood=Mood.BAD)
            result = False

        #  check if the last file name in the processed sequence is right
        last_file_name = int(max(os.scandir(self.path), key=lambda entry: int(os.path.splitext(entry.name)[0])).name.split('.')[0])
        if self.frames_count != last_file_name:
            self.update_status(message=f"Last processed frame is {last_file_name}, but expected {self.frames_count}. Check in {self.path} for it.", mood=Mood.BAD)
            result = False
        #  check if all frames are non zero-sized
        zero_sized_files_count = 0
        for file_path in self.processed_frames:
            if os.path.getsize(file_path) == 0:
                zero_sized_files_count += 1
        if zero_sized_files_count > 0:
            self.update_status(message=f"There is zero-sized files in {self.path} temp directory ({zero_sized_files_count} of {processed_frames_count}). Check for free disk space and access rights.", mood=Mood.BAD)
            result = False
        return result
