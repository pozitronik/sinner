import glob
import os.path

import cv2
from cv2 import VideoCapture

from roop.handlers.video.BaseVideoHandler import BaseVideoHandler
from roop.typing import Frame
from roop.utilities import write_image


class CV2VideoHandler(BaseVideoHandler):

    def open(self) -> VideoCapture:
        cap = cv2.VideoCapture(self._target_path)
        if not cap.isOpened():
            raise Exception("Error opening video file")
        return cap

    def detect_fps(self) -> float:
        capture = self.open()
        fps = capture.get(cv2.CAP_PROP_FPS)
        capture.release()
        return fps

    def detect_fc(self) -> int:
        capture = self.open()
        video_frame_total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        capture.release()
        return video_frame_total

    def extract_frames(self, to_dir: str) -> None:
        capture = self.open()
        i = 1
        while True:
            ret, frame = capture.read()
            if not ret: break
            write_image(frame, os.path.join(to_dir, f"{i:04d}.png"))
            i += 1
        capture.release()

    def extract_frame(self, frame_number: int) -> Frame:
        capture = self.open()
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = capture.read()
        capture.release()
        if not ret:
            raise Exception(f"Error reading frame {frame_number}")
        return frame

    def create_video(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> None:
        if None == fps: fps = self.fps
        if None != audio_target: print('Sound is not supported in CV2VideoHandler')
        frame_files = glob.glob(os.path.join(glob.escape(from_dir), '*.png'))
        first_frame = cv2.imread(frame_files[0])
        height, width, channels = first_frame.shape
        fourcc = cv2.VideoWriter_fourcc(*'H264')  # Specify the video codec
        video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        for frame_path in frame_files:
            frame = cv2.imread(frame_path)
            video_writer.write(frame)

        video_writer.release()
