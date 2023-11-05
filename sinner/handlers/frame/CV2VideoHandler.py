import glob
import os.path
from pathlib import Path
from typing import List

import cv2
from cv2 import VideoCapture
from tqdm import tqdm

from sinner.Status import Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.EOutOfRange import EOutOfRange
from sinner.helpers.FrameHelper import write_to_image, read_from_image
from sinner.models.NumberedFrame import NumberedFrame
from sinner.typing import NumeratedFramePath, Frame
from sinner.utilities import get_file_name
from sinner.validators.AttributeLoader import Rules


class CV2VideoHandler(BaseFrameHandler):
    emoji: str = '📹'

    output_fps: float

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'output-fps',
                'default': lambda: self.fps,
                'help': 'FPS of resulting video'
            },
            {
                'module_help': 'The video processing module, based on CV2 library'
            }
        ]

    @staticmethod
    def available() -> bool:
        return "FFMPEG" in cv2.getBuildInformation()

    def open(self) -> VideoCapture:
        cap = cv2.VideoCapture(self._target_path)
        if not cap.isOpened():
            raise Exception("Error opening frame file")
        return cap

    @property
    def fps(self) -> float:
        if self._fps is None:
            capture = self.open()
            self._fps = capture.get(cv2.CAP_PROP_FPS)
            capture.release()
        return self._fps

    @property
    def fc(self) -> int:  # this value can be inaccurate
        def is_frame_readable(position: int) -> bool:
            capture.set(cv2.CAP_PROP_POS_FRAMES, position - 1)
            return capture.read()[0]

        if self._fc is None:
            capture = self.open()
            header_frames_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if is_frame_readable(header_frames_count):
                self._fc = header_frames_count
                return self._fc
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
            self._fc = last_good_position
        return self._fc

    @property
    def resolution(self) -> tuple[int, int] | None:
        if self._resolution is None:
            capture = self.open()
            self._resolution = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            capture.release()
        return self._resolution

    def get_frames_paths(self, path: str, frames_range: tuple[int | None, int | None] = (None, None)) -> List[NumeratedFramePath]:
        start = frames_range[0] if frames_range[0] is not None else 0
        stop = frames_range[1] if frames_range[1] is not None else self.fc - 1
        #  fixme: do not ignore, if frames already ignored over the frame index
        with tqdm(
                total=stop,
                desc='Extracting frame',
                unit='frame',
                dynamic_ncols=True,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
                initial=start
        ) as progress:
            capture = self.open()
            capture.set(cv2.CAP_PROP_POS_FRAMES, start)
            filename_length = len(str(self.fc))  # a way to determine frame names length
            Path(path).mkdir(parents=True, exist_ok=True)
            while start <= stop:
                frame: Frame
                ret, frame = capture.read()
                if not ret:
                    break
                filename: str = os.path.join(path, str(start).zfill(filename_length) + ".png")
                if write_to_image(frame, filename) is False:
                    raise Exception(f"Error writing {frame.nbytes} bytes to {filename}")
                progress.update()
                start += 1
            capture.release()
            frames_path = sorted(glob.glob(os.path.join(glob.escape(path), '*.png')))
            return [(int(get_file_name(file_path)), file_path) for file_path in frames_path if os.path.isfile(file_path)]

    def extract_frame(self, frame_number: int) -> NumberedFrame:
        if frame_number >= self.fc:
            raise EOutOfRange(frame_number, 0, self.fc-1)
        capture = self.open()
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)  # zero-based frames
        ret, frame = capture.read()
        capture.release()
        if not ret:
            raise Exception(f"Error reading frame {frame_number}")
        return NumberedFrame(frame_number, frame)

    def result(self, from_dir: str, filename: str, audio_target: str | None = None) -> bool:
        self.update_status(f"Resulting frames from {from_dir} to {filename} with {self.output_fps} FPS")
        if audio_target is not None:
            self.update_status(message='Sound copying is not supported in CV2VideoHandler', mood=Mood.NEUTRAL)
        try:
            Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
            frame_files = glob.glob(os.path.join(glob.escape(from_dir), '*.png'))
            first_frame = read_from_image(frame_files[0])
            height, width, channels = first_frame.shape
            fourcc = self.suggest_codec()
            video_writer = cv2.VideoWriter(filename, fourcc, self.output_fps, (width, height))
            for frame_path in frame_files:
                frame = read_from_image(frame_path)
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
