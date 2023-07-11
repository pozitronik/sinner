from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.handlers.frame.FFmpegVideoHandler import FFmpegVideoHandler
from sinner.processors.BaseValidatedClass import Rules


class VideoHandler(CV2VideoHandler):
    with_fps: float
    keep_audio: bool = False
    keep_frames: bool = False
    extract_frames: bool = False

    fps: float
    fc: int
    _target_path: str
    current_frame_index: int = 0

    def rules(self) -> Rules:
        return [
            {'parameter': 'with-fps', 'required': False},
            {'parameter': 'keep-audio', 'required': False},
            {'parameter': 'keep-frames', 'required': False},
            {'parameter': 'extract-frames', 'required': False},
        ]

    def result(self, from_dir: str, filename: str, fps: None | float = None, audio_target: str | None = None) -> bool:
        if audio_target is not None:
            return FFmpegVideoHandler(self._target_path).result(from_dir, filename, fps, audio_target)
        return super().result(from_dir, filename, fps, audio_target)
