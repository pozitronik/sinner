import os
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import List

import cv2
from numpy import uint8, frombuffer

from sinner.Status import Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.validators.AttributeLoader import Rules


class FFmpegVideoHandler(BaseFrameHandler):
    output_fps: float

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': 'output-fps',
                'default': self.fps,
                'help': 'FPS of resulting video'
            },
        ]

    def run(self, args: List[str]) -> bool:
        commands = ['ffmpeg', '-y', '-hide_banner', '-hwaccel', 'auto', '-loglevel', 'verbose', '-progress', 'pipe:1']
        commands.extend(args)
        self.update_status(message=' '.join(commands), mood=Mood.NEUTRAL)
        try:
            subprocess.check_output(commands, stderr=subprocess.STDOUT)
            return True
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            pass
        return False

    @staticmethod
    def available() -> bool:
        return shutil.which('ffmpeg') is not None

    def __init__(self, target_path: str, parameters: Namespace):
        if not self.available():
            raise Exception('ffmpeg is not installed. Install it or use --frame-handler=cv2')

        super().__init__(target_path, parameters)

    @property
    def fps(self) -> float:
        if self._fps is None:
            command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=avg_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', self._target_path]
            output = subprocess.check_output(command).decode().strip().split('/')
            try:
                numerator, denominator = map(int, output)
                self._fps = numerator / denominator
            except Exception as exception:
                self.update_status(message=str(exception), mood=Mood.BAD)
                self._fps = 30.0
        return self._fps

    @property
    def fc(self) -> int:
        if self._fc is None:
            try:
                command = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames', '-of', 'default=nokey=1:noprint_wrappers=1', self._target_path]
                output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode('utf-8').strip()  # can be very slow!
                if 'N/A' == output:
                    return 1  # non-frame files, still processable
                self._fc = int(output)
            except Exception as exception:
                self.update_status(message=str(exception), mood=Mood.BAD)
                self._fc = 0
        return self._fc

    def get_frames_paths(self, path: str, frames_range: tuple[int | None, int | None] = (None, None)) -> List[NumeratedFramePath]:
        filename_length = len(str(self.fc))  # a way to determine frame names length
        Path(path).mkdir(parents=True, exist_ok=True)
        start_frame = frames_range[0] if frames_range[0] is not None else 0
        stop_frame = frames_range[1] if frames_range[1] is not None else self.fc
        self.run(['-i', self._target_path, '-vf', f"select='between(n,{start_frame},{stop_frame})'", '-vsync', '0', '-pix_fmt', 'rgb24', '-frame_pts', '1', os.path.join(path, f'%{filename_length}d.png')])
        return super().get_frames_paths(path)

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        command = ['ffmpeg', '-i', self._target_path, '-pix_fmt', 'rgb24', '-vf', f"select='eq(n,{frame_number})',setpts=N/FRAME_RATE/TB", '-vframes', '1', '-f', 'image2pipe', '-c:v', 'png', '-']
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        return frame_number, cv2.imdecode(frombuffer(output, uint8), cv2.IMREAD_COLOR), None

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        self.update_status(f"Resulting frames from {from_dir} to {filename} with {self.output_fps} FPS")
        filename_length = len(str(self.fc))  # a way to determine frame names length
        Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
        command = ['-r', str(self.output_fps), '-i', os.path.join(from_dir, f'%0{filename_length}d.png'), '-c:v', 'h264_nvenc', '-preset', 'medium', '-qp', '18', '-pix_fmt', 'yuv420p', '-vf',
                   'colorspace=bt709:iall=bt601-6-625:fast=1', filename]
        if audio_target:
            command.extend(['-i', audio_target, '-shortest'])
        return self.run(command)
