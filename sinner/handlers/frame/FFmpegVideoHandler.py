import math
import os
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import List

import cv2
from numpy import uint8, frombuffer

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.EOutOfRange import EOutOfRange
from sinner.models.NumberedFrame import NumberedFrame
from sinner.models.status.Mood import Mood
from sinner.typing import NumeratedFramePath
from sinner.validators.AttributeLoader import Rules


class FFmpegVideoHandler(BaseFrameHandler):
    emoji: str = '🎥'

    output_fps: float
    ffmpeg_resulting_parameters: str

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'output-fps',
                'default': self.fps,
                'help': 'FPS of resulting video'
            },
            {
                'parameter': ['ffmpeg_resulting_parameters'],
                'default': '-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p',
                'help': 'ffmpeg command-line part to adjust resulting video parameters'
            },
            {
                'module_help': 'The video processing module, based on ffmpeg'
            }
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
        def is_frame_readable(position: int) -> bool:
            return 'nothing was encoded' not in subprocess.check_output(['ffmpeg', '-i', self._target_path, '-vf', f"select='eq(n,{position - 1})", '-f', 'null', '-'], stderr=subprocess.STDOUT).decode().strip()  # zer-based index

        def find_last_frame(total_frames: int) -> int:
            if is_frame_readable(total_frames):
                return total_frames

            left = 1
            right = total_frames
            last_good = 0

            while left <= right:
                mid = (left + right) // 2
                if is_frame_readable(mid):
                    last_good = mid
                    left = mid + 1
                else:
                    right = mid - 1

            return last_good

        if self._fc is None:
            try:
                command = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames', '-of', 'default=nokey=1:noprint_wrappers=1', self._target_path]
                output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()  # can be very slow!
                if 'N/A' == output:
                    return 1  # non-frame files, still processable
                self._fc = find_last_frame(int(output))
            except Exception as exception:
                self.update_status(message=str(exception), mood=Mood.BAD)
                self._fc = 0
        return self._fc

    @property
    def resolution(self) -> tuple[int, int]:
        if self._resolution is None:
            try:
                command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', self._target_path]
                output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()  # can be very slow!
                if 'N/A' == output:
                    self._resolution = (0, 0)  # non-frame files, still processable
                w, h = output.split('x')
                self._resolution = int(w), int(h)
            except Exception as exception:
                self.update_status(message=str(exception), mood=Mood.BAD)
                self._resolution = 0, 0
        return self._resolution

    def get_frames_paths(self, path: str, frames_range: tuple[int | None, int | None] = (None, None)) -> List[NumeratedFramePath]:
        filename_length = len(str(self.fc))  # a way to determine frame names length
        Path(path).mkdir(parents=True, exist_ok=True)
        start_frame = frames_range[0] if frames_range[0] is not None else 0
        stop_frame = frames_range[1] if frames_range[1] is not None else self.fc
        self.run(['-i', self._target_path, '-vf', f"select='between(n,{start_frame},{stop_frame})'", '-vsync', '0', '-pix_fmt', 'rgb24', '-frame_pts', '1', os.path.join(path, f'%{filename_length}d.png')])
        return super().get_frames_paths(path)

    def extract_frame(self, frame_number: int) -> NumberedFrame:
        if frame_number > self.fc:
            raise EOutOfRange(frame_number, 0, self.fc)
        command = ['ffmpeg', '-i', self._target_path, '-pix_fmt', 'rgb24', '-vf', f"select='eq(n,{frame_number})',setpts=N/FRAME_RATE/TB", '-vframes', '1', '-f', 'image2pipe', '-c:v', 'png', '-']
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        return NumberedFrame(frame_number, cv2.imdecode(frombuffer(output, uint8), cv2.IMREAD_COLOR))

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        self.update_status(f"Resulting frames from {from_dir} to {filename} with {self.output_fps} FPS")
        filename_length = len(str(self.fc))  # a way to determine frame names length
        Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
        command = ['-framerate', str(self.output_fps), '-i', os.path.join(from_dir, f'%0{filename_length}d.png')]
        command.extend(self.ffmpeg_resulting_parameters.split(' '))
        command.extend(['-r', str(self.output_fps), filename])
        if audio_target:
            command.extend(['-i', audio_target, '-shortest'])
        return self.run(command)
