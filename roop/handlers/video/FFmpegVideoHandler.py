import os
import shutil
import subprocess
from typing import List

import cv2
from numpy import uint8, frombuffer

from roop.handlers.video.BaseVideoHandler import BaseVideoHandler
from roop.typing import Frame


class FFmpegVideoHandler(BaseVideoHandler):

    def __init__(self, target_path: str):
        if not shutil.which('ffmpeg'):
            raise Exception('ffmpeg is not installed. Install it or use --video-handler=cv2')

        super().__init__(target_path)

    def run(self, args: List[str]) -> bool:
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

    def detect_fc(self) -> int:
        command = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames', '-of', 'default=nokey=1:noprint_wrappers=1', self._target_path]
        output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode('utf-8').strip()
        return int(output)

    def extract_frames(self, to_dir: str) -> None:
        self.run(['-i', self._target_path, '-pix_fmt', 'rgb24', os.path.join(to_dir, '%04d.png')])

    def extract_frame(self, frame_number: int) -> tuple[Frame, int]:
        command = ['ffmpeg', '-i', self._target_path, '-pix_fmt', 'rgb24', '-vf', f"select=gte(n\,{frame_number}),setpts=N/FRAME_RATE/TB", '-vframes', '1', '-f', 'image2pipe', '-c:v', 'png', '-']
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        return cv2.imdecode(frombuffer(output, uint8), cv2.IMREAD_COLOR), frame_number

    def create_video(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> None:
        if None == fps: fps = self.fps
        command = ['-r', str(fps), '-i', os.path.join(from_dir, '%04d.png'), '-c:v', 'h264_nvenc', '-preset', 'medium', '-qp', '18', '-pix_fmt', 'yuv420p', '-vf', 'colorspace=bt709:iall=bt601-6-625:fast=1', filename]
        if audio_target: command.extend(['-i', audio_target, '-shortest'])
        self.run(command)
