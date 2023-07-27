import glob
import os.path
import platform
from pathlib import Path
from typing import List

import cv2
from cv2 import VideoCapture
from numpy import fromfile, uint8
from tqdm import tqdm

from sinner.Status import Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import NumeratedFrame, NumeratedFramePath, Frame
from sinner.utilities import get_file_name
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
        def is_frame_readable(position: int) -> bool:
            capture.set(cv2.CAP_PROP_POS_FRAMES, position - 1)
            return capture.read()[0]

        capture = self.open()
        header_frames_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if is_frame_readable(header_frames_count):
            return header_frames_count
        else:  # cv2.CAP_PROP_FRAME_COUNT returns value from the video header, which not always correct, so we can find the right value via binary search
            last_good_position = 1
            last_bad_position = header_frames_count
            current_position = int((last_bad_position - last_good_position) / 2)
            while last_bad_position - last_good_position > 1:
                if is_frame_readable(current_position):
                    last_good_position = current_position
                    current_position += int((last_bad_position - last_good_position) / 2)
                else:
                    last_bad_position = current_position
                    current_position -= int((last_bad_position - last_good_position) / 2)

        capture.release()
        return last_good_position

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
                frame: Frame
                ret, frame = capture.read()
                if not ret:
                    break
                filename: str = os.path.join(path, str(i + 1).zfill(filename_length) + ".png")
                if self.write_image(frame, filename) is False:
                    raise Exception(f"Error writing {frame.nbytes} bytes to {filename}")
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
            first_frame = self.read_image(frame_files[0])
            height, width, channels = first_frame.shape
            fourcc = self.suggest_codec()
            video_writer = cv2.VideoWriter(filename, fourcc, self.output_fps, (width, height))
            for frame_path in frame_files:
                frame = self.read_image(frame_path)
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

    @staticmethod
    def read_image(path: str) -> Frame:
        if platform.system().lower() == 'windows':  # issue #511
            image = cv2.imdecode(fromfile(path, dtype=uint8), cv2.IMREAD_UNCHANGED)
            if image.shape[2] == 4:  # fixes the alpha-channel issue
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            return image
        else:
            return cv2.imread(path)

    @staticmethod
    def write_image(image: Frame, path: str) -> bool:
        if platform.system().lower() == 'windows':  # issue #511
            is_success, im_buf_arr = cv2.imencode(".png", image)
            im_buf_arr.tofile(path)
            return is_success
        else:
            return cv2.imwrite(path, image)
