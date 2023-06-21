import os
import subprocess
from typing import List

from roop.parameters import Parameters
from roop.state import State
from roop.utilities import get_temp_directory_path, get_temp_output_path, move_temp


class FFMPEG:
    _target_path: str

    def __init__(self, params: Parameters):
        self._target_path = params.target_path


    def run_ffmpeg(self, args: List[str]) -> bool:
        commands = ['ffmpeg', '-hide_banner', '-hwaccel', 'auto', '-loglevel', 'verbose']
        commands.extend(args)
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
        except Exception:
            pass
        return 30.0

    def extract_frames(self) -> None:
        temp_directory_path = get_temp_directory_path(self._target_path)
        self.run_ffmpeg(['-i', self._target_path, '-pix_fmt', 'rgb24', os.path.join(temp_directory_path, '%04d.png')])

    def create_video(self,  fps: float = 30.0) -> None:
        temp_output_path = get_temp_output_path(self._target_path)
        temp_directory_path = get_temp_directory_path(self._target_path)
        self.run_ffmpeg(['-r', str(fps), '-i', os.path.join(temp_directory_path, State.PROCESSED_PREFIX + '%04d.png'), '-c:v', 'h264_nvenc', '-preset', 'medium', '-qp', '18', '-pix_fmt', 'yuv420p', '-vf',
                         'colorspace=bt709:iall=bt601-6-625:fast=1', '-y', temp_output_path])

    def restore_audio(self, output_path: str) -> None:
        temp_output_path = get_temp_output_path(self._target_path)
        done = self.run_ffmpeg(['-i', temp_output_path, '-i', self._target_path, '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0', '-y', output_path])
        if not done:
            move_temp(self._target_path, output_path)
