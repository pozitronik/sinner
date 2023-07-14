from argparse import Namespace

from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.handlers.frame.FFmpegVideoHandler import FFmpegVideoHandler
from sinner.validators.AttributeLoader import Rules


class VideoHandler(CV2VideoHandler):
    keep_audio: bool

    fps: float
    fc: int
    _target_path: str
    current_frame_index: int = 0

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': 'keep-audio',
                'default': False,
                'help': 'Keep original audio'
            }
        ]

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        if audio_target is not None and self.keep_audio:
            return FFmpegVideoHandler(self._target_path, Namespace()).result(from_dir, filename, audio_target)
        return super().result(from_dir, filename, audio_target)
