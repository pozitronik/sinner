import os.path
import shutil
from pathlib import Path
from typing import List

from sinner.Status import Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.EOutOfRange import EOutOfRange
from sinner.helpers.FrameHelper import read_from_image
from sinner.models.NumberedFrame import NumberedFrame
from sinner.typing import NumeratedFramePath
from sinner.utilities import is_image
from sinner.validators.AttributeLoader import Rules


class ImageHandler(BaseFrameHandler):
    emoji: str = '🖼️'

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'target-path',
                'attribute': '_target_path',
                'valid': lambda: os.path.exists(self._target_path) and os.path.isfile(self._target_path) and is_image(self._target_path),
                'help': 'Select an image file'
            },
            {
                'module_help': 'The module for processing image files'
            }
        ]

    @property
    def fps(self) -> float:
        return 1

    @property
    def fc(self) -> int:
        return 1

    @property
    def resolution(self) -> tuple[int, int] | None:
        if self._resolution is None:
            image = read_from_image(self._target_path)
            self._resolution = image.shape[1], image.shape[0]
        return self._resolution

    def get_frames_paths(self, path: str, frames_range: tuple[int | None, int | None] = (None, None)) -> List[NumeratedFramePath]:
        return [(0, self._target_path)]

    def extract_frame(self, frame_number: int) -> NumberedFrame:
        if frame_number >= self.fc:
            raise EOutOfRange(frame_number, 0, self.fc-1)
        return NumberedFrame(frame_number, read_from_image(self._target_path))

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        try:
            result_file = os.path.join(from_dir, os.listdir(from_dir).pop())
            self.update_status(f"Copy frame from {result_file} to {filename}")
            Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
            # fixme: there can by other files in the from_dir
            shutil.copyfile(result_file, filename)
            return True
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            return False
