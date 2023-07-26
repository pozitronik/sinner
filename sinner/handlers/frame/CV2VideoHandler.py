import glob
import os.path
from pathlib import Path
from typing import List

import cv2
from cv2 import VideoCapture
from tqdm import tqdm

from sinner.Status import Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import NumeratedFrame, NumeratedFramePath
from sinner.utilities import write_image, get_file_name
from sinner.validators.AttributeLoader import Rules


class CV2VideoHandler(BaseFrameHandler):
    output_fps: float

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': 'output-fps',
                'default': self.fps,
                'help': 'FPS of resulting video'
            },
        ]

    @staticmethod
    def available() -> bool:
        return "FFMPEG" in cv2.getBuildInformation()

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

    def detect_fc(self) -> int:  # this value can be inaccurate
        capture = self.open()
        frames_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        search_position = frames_count
        step = int(search_position / 20) + 1
        initial_step = step
        backward = True
        last_ret = False
        while True:  # cv2.CAP_PROP_FRAME_COUNT returns value from the video header, which not always correct, so we can find the right value via binary search
            capture.set(cv2.CAP_PROP_POS_FRAMES, search_position - 1)
            ret, _ = capture.read()
            if (step == 1 or step == initial_step) and ret is True and last_ret is False:
                break
            if last_ret != ret:
                step = int(step / 2)
                if step == 0:
                    step = 1
                backward = not backward
            last_ret = ret
            search_position = search_position - step if backward else search_position + step
            if search_position > frames_count:
                search_position = frames_count
        capture.release()
        return search_position

    def get_frames_paths(self, path: str) -> List[NumeratedFramePath]:
        fc = self.fc
        i = self.current_frame_index
        #  fixme: do not ignore, if frames already ignored over the frame index
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

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        self.update_status(f"Resulting frames from {from_dir} to {filename} with {self.output_fps} FPS")
        if audio_target is not None:
            self.update_status(message='Sound copying is not supported in CV2VideoHandler', mood=Mood.NEUTRAL)
        try:
            Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
            frame_files = glob.glob(os.path.join(glob.escape(from_dir), '*.png'))
            first_frame = cv2.imread(frame_files[0])
            height, width, channels = first_frame.shape
            fourcc = self.suggest_codec()
            video_writer = cv2.VideoWriter(filename, fourcc, self.output_fps, (width, height))
            for frame_path in frame_files:
                frame = cv2.imread(frame_path)
                video_writer.write(frame)
            video_writer.release()
            return True
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            return False

    def suggest_codec(self) -> int:
        codecs_strings = ["H264", "X264", "DIVX", "XVID", "MJPG", "WMV1", "WMV2", "FMP4", "mp4v", "avc1", "I420", "IYUV", "mpg1", ]
        for codec in codecs_strings:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            if 0 != fourcc:
                self.update_status(message=f"Suggested codec: {fourcc}", mood=Mood.NEUTRAL)
                return fourcc
        raise NotImplementedError('No supported codecs found')
