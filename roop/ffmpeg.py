import os
import subprocess
from typing import List

from roop.parameters import Parameters


class FFMPEG:
    fps: float
    _target_path: str

    def __init__(self, params: Parameters):
        self._target_path = params.target_path
        self.fps = self.detect_fps()

    def run_ffmpeg(self, args: List[str]) -> bool:
        commands = ['ffmpeg', '-y', '-hide_banner', '-hwaccel', 'auto', '-loglevel', 'verbose']
        commands.extend(args)
        print(' '.join(commands))
        try:
            subprocess.check_output(commands, stderr=subprocess.STDOUT)
            return True
        except Exception as exception:
            print(exception)
            pass
        return False

    def detect_fps(self) -> float:
        command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', self._target_path]
        output = subprocess.check_output(command).decode().strip().split('/')
        try:
            numerator, denominator = map(int, output)
            return numerator / denominator
        except Exception as exception:
            print(exception)
            pass
        return 30.0

    def extract_frames(self, to_dir: str) -> None:
        self.run_ffmpeg(['-i', self._target_path, '-pix_fmt', 'rgb24', os.path.join(to_dir, '%04d.png')])

    def create_video(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> None:
        if None == fps: fps = self.fps
        command = ['-r', str(fps), '-i', os.path.join(from_dir, '%04d.png'), '-c:v', 'h264_nvenc', '-preset', 'medium', '-qp', '18', '-pix_fmt', 'yuv420p', '-vf', 'colorspace=bt709:iall=bt601-6-625:fast=1', filename]
        if audio_target: command.extend(['-i', audio_target, '-shortest'])
        self.run_ffmpeg(command)
