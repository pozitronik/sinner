import os
import shutil
import subprocess
from typing import List

import cv2
from numpy import uint8, frombuffer

from roop.handlers.frames.BaseFramesHandler import BaseFramesHandler
from roop.typing import Frame


class FFmpegVideoHandler(BaseFramesHandler):

    @staticmethod
    def run(args: List[str]) -> bool:
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

    @staticmethod
    def available() -> bool:
        return shutil.which('ffmpeg') is not None

    def __init__(self, target_path: str):
        if not self.available():
            raise Exception('ffmpeg is not installed. Install it or use --frames-handler=cv2')

        super().__init__(target_path)

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
        try:
            command = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames', '-of', 'default=nokey=1:noprint_wrappers=1', self._target_path]
            output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode('utf-8').strip()
            if 'N/A' == output:
                return 1  # non-frames files, still processable
            return int(output)
        except Exception as exception:
            print(exception)
            return 0

    def get_frames_paths(self, path: str) -> List[tuple[int, str]]:
        filename_length = len(str(self.detect_fc()))  # a way to determine frame names length
        self.run(['-i', self._target_path, '-pix_fmt', 'rgb24', os.path.join(path, f'%{filename_length}d.png')])
        return super().get_frames_paths(path)

    def extract_frame(self, frame_number: int) -> tuple[Frame, int]:
        command = ['ffmpeg', '-i', self._target_path, '-pix_fmt', 'rgb24', '-vf', f"select=gte(n,{frame_number}),setpts=N/FRAME_RATE/TB", '-vframes', '1', '-f', 'image2pipe', '-c:v', 'png', '-']
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        return cv2.imdecode(frombuffer(output, uint8), cv2.IMREAD_COLOR), frame_number

    # todo: method will fail if save path is not existed
    def result(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> bool:
        if fps is None:
            fps = self.fps
        filename_length = len(str(self.detect_fc()))  # a way to determine frame names length
        command = ['-r', str(fps), '-i', os.path.join(from_dir, f'%0{filename_length}d.png'), '-c:v', 'h264_nvenc', '-preset', 'medium', '-qp', '18', '-pix_fmt', 'yuv420p', '-vf',
                   'colorspace=bt709:iall=bt601-6-625:fast=1', filename]
        if audio_target:
            command.extend(['-i', audio_target, '-shortest'])
        return self.run(command)
