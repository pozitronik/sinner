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
        commands = ['ffmpeg', '-y', '-hide_banner', '-hwaccel', 'auto', '-loglevel', 'verbose']
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

    def detect_fps(self) -> float:
        command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=avg_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', self._target_path]
        output = subprocess.check_output(command).decode().strip().split('/')
        try:
            numerator, denominator = map(int, output)
            return numerator / denominator
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            pass
        return 30.0

    def detect_fc(self) -> int:
        try:
            command = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames', '-of', 'default=nokey=1:noprint_wrappers=1', self._target_path]
            output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode('utf-8').strip()  # can be very slow!
            if 'N/A' == output:
                return 1  # non-frame files, still processable
            return int(output)
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            return 0

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        filename_length = len(str(self.detect_fc()))  # a way to determine frame names length
        Path(path).mkdir(parents=True, exist_ok=True)
        self.run(['-i', self._target_path, '-pix_fmt', 'rgb24', os.path.join(path, f'%{filename_length}d.png')])
        return super().get_frames_paths(path)

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        command = ['ffmpeg', '-i', self._target_path, '-pix_fmt', 'rgb24', '-vf', f"select='eq(n,{frame_number})',setpts=N/FRAME_RATE/TB", '-vframes', '1', '-f', 'image2pipe', '-c:v', 'png', '-']
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        return frame_number, cv2.imdecode(frombuffer(output, uint8), cv2.IMREAD_COLOR)

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        self.update_status(f"Resulting frames from {from_dir} to {filename} with {self.output_fps} FPS")
        filename_length = len(str(self.detect_fc()))  # a way to determine frame names length
        Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
        command = ['-r', str(self.output_fps), '-i', os.path.join(from_dir, f'%0{filename_length}d.png'), '-c:v', 'h264_nvenc', '-preset', 'medium', '-qp', '18', '-pix_fmt', 'yuv420p', '-vf',
                   'colorspace=bt709:iall=bt601-6-625:fast=1', filename]
        if audio_target:
            command.extend(['-i', audio_target, '-shortest'])
        return self.run(command)
