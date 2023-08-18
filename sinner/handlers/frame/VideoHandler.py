from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.handlers.frame.FFmpegVideoHandler import FFmpegVideoHandler
from sinner.validators.AttributeLoader import Rules


class VideoHandler(CV2VideoHandler, FFmpegVideoHandler):
    emoji: str = '🎥'

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
            },
            {
                'module_help': 'The combined video processing module'
            }
        ]

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        if FFmpegVideoHandler.available():
            return FFmpegVideoHandler.result(self, from_dir, filename, audio_target)
        return super().result(from_dir, filename, audio_target)
