from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.handlers.frame.FFmpegVideoHandler import FFmpegVideoHandler


class VideoHandler(CV2VideoHandler):

    def result(self, from_dir: str, filename: str, fps: None | float = None, audio_target: str | None = None) -> bool:
        if audio_target is not None:
            return FFmpegVideoHandler(self._target_path).result(from_dir, filename, fps, audio_target)
        return super().result(from_dir, filename, fps, audio_target)
