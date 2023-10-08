import os.path
import shutil
from pathlib import Path
from typing import List

from sinner.Status import Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.utilities import is_image
from sinner.validators.AttributeLoader import Rules


class ImageHandler(BaseFrameHandler):
    emoji: str = '🖼️'

    def rules(self) -> Rules:
        super().rules()
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

    def get_frames_paths(self, path: str, frames_range: tuple[int | None, int | None] = (None, None)) -> List[NumeratedFramePath]:
        return [(0, self._target_path)]

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        return frame_number, CV2VideoHandler.read_image(self._target_path), None

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
