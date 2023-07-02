import glob
import os.path
from pathlib import Path
from typing import List

import cv2
from cv2 import VideoCapture
from tqdm import tqdm

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.utilities import write_image, get_file_name


class CV2VideoHandler(BaseFrameHandler):

    def open(self) -> VideoCapture:
        cap = cv2.VideoCapture(self._target_path)
        if not cap.isOpened():
            raise Exception("Error opening frame file")
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

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        fc = self.detect_fc()
        i = self.current_frame_index
        with tqdm(
                total=self.fc,
                desc='Extracting frame',
                unit='frame',
                dynamic_ncols=True,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
                initial=i
        ) as progress:
            capture = self.open()
            capture.set(cv2.CAP_PROP_POS_FRAMES, i)
            filename_length = len(str(fc))  # a way to determine frame names length
            Path(path).mkdir(parents=True, exist_ok=True)
            while True or i <= fc:
                ret, frame = capture.read()
                if not ret:
                    break
                write_image(frame, os.path.join(path, str(i + 1).zfill(filename_length) + ".png"))
                progress.update()
                i += 1
            capture.release()
            frames_path = sorted(glob.glob(os.path.join(glob.escape(path), '*.png')))
            all_files = [(int(get_file_name(file_path)), file_path) for file_path in frames_path]
            return [t for t in all_files if t[0] > self.current_frame_index]

    def extract_frame(self, frame_number: int) -> NumeratedFrame:
        capture = self.open()
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)  # zero-based frames
        ret, frame = capture.read()
        capture.release()
        if not ret:
            raise Exception(f"Error reading frame {frame_number}")
        return frame_number, frame

    def result(self, from_dir: str, filename: str, fps: None | float = None, audio_target: str | None = None) -> bool:
        if fps is None:
            fps = self.fps
        if audio_target is not None:
            print('Sound is not supported in CV2VideoHandler')
        try:
            Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
            frame_files = glob.glob(os.path.join(glob.escape(from_dir), '*.png'))
            first_frame = cv2.imread(frame_files[0])
            height, width, channels = first_frame.shape
            fourcc = self.suggest_codec()
            video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
            for frame_path in frame_files:
                frame = cv2.imread(frame_path)
                video_writer.write(frame)
            video_writer.release()
            return True
        except Exception:
            return False

    @staticmethod
    def suggest_codec() -> int:
        codecs_strings = ["H264", "X264", "DIVX", "XVID", "MJPG", "WMV1", "WMV2", "FMP4", "mp4v", "avc1", "I420", "IYUV", "mpg1", ]
        for codec in codecs_strings:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            if 0 != fourcc:
                return fourcc
        raise NotImplementedError('No supported codecs found')
