import glob
import os.path
from pathlib import Path
from typing import List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import cv2
import psutil
from cv2 import VideoCapture
from tqdm import tqdm

from sinner.models.logger.Mood import Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.EOutOfRange import EOutOfRange
from sinner.helpers.FrameHelper import write_to_image, read_from_image
from sinner.models.NumberedFrame import NumberedFrame
from sinner.typing import NumeratedFramePath, Frame
from sinner.utilities import get_file_name, is_file, get_mem_usage, suggest_max_memory
from sinner.validators.AttributeLoader import Rules


class CV2VideoHandler(BaseFrameHandler):
    emoji: str = '📹'

    output_fps: float
    max_memory: int

    _statistics: dict[str, int] = {'mem_rss_max': 0, 'mem_vms_max': 0, 'limits_reaches': 0}

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'output-fps',
                'default': lambda: self.fps,
                'help': 'FPS of resulting video'
            },
            {
                'parameter': 'max-memory',  # key defined in Sin, but class can be called separately in tests
                'default': suggest_max_memory(),
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
    def resolution(self) -> tuple[int, int]:
        if self._resolution is None:
            capture = self.open()
            self._resolution = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            capture.release()
        return self._resolution

    def get_frames_paths(self, path: str, frames_range: tuple[int | None, int | None] = (None, None)) -> List[NumeratedFramePath]:
        def write_done(future_: Future[bool]) -> None:
            futures.remove(future_)
            progress.set_postfix(self.get_postfix(len(futures)))
            progress.update()

        start = frames_range[0] if frames_range[0] is not None else 0
        stop = frames_range[1] if frames_range[1] is not None else self.fc - 1

        with ThreadPoolExecutor(max_workers=psutil.cpu_count()) as executor:  # use one worker per cpu core
            futures: list[Future[bool]] = []
            future_to_frame = {}
            capture = self.open()
            capture.set(cv2.CAP_PROP_POS_FRAMES, start)
            filename_length = len(str(self.fc))
            Path(path).mkdir(parents=True, exist_ok=True)

            # Initialize the progress bar
            with tqdm(
                    total=stop,
                    desc='Extracting frame',
                    unit='frame',
                    dynamic_ncols=True,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
                    initial=start
            ) as progress:
                for frame_index in range(start, stop + 1):
                    frame: Frame
                    ret, frame = capture.read()
                    if not ret:
                        break
                    filename: str = os.path.join(path, str(frame_index).zfill(filename_length) + ".png")
                    # Submit only the write_to_image function to the executor, excluding it processing time from the loop
                    future: Future[bool] = executor.submit(write_to_image, frame, filename)
                    future.add_done_callback(write_done)
                    futures.append(future)
                    progress.set_postfix(self.get_postfix(len(futures)))
                    future_to_frame[future] = frame_index  # Keep track of which frame the future corresponds to
                    if get_mem_usage('vms', 'g') >= self.max_memory:
                        futures[:1][0].result()
                        self._statistics['limits_reaches'] += 1

                for future in as_completed(future_to_frame):
                    frame_index = future_to_frame[future]
                    try:
                        if not future.result():
                            raise Exception(f"Error writing frame {frame_index}")
                    except Exception as exc:
                        print(f'Frame {frame_index} generated an exception: {exc}')

                capture.release()

        frames_path = sorted(glob.glob(os.path.join(glob.escape(path), '*.png')))
        return [(int(get_file_name(file_path)), file_path) for file_path in frames_path if is_file(file_path)]

    def get_mem_usage(self) -> str:
        mem_rss = get_mem_usage()
        mem_vms = get_mem_usage('vms')
        if self._statistics['mem_rss_max'] < mem_rss:
            self._statistics['mem_rss_max'] = mem_rss
        if self._statistics['mem_vms_max'] < mem_vms:
            self._statistics['mem_vms_max'] = mem_vms
        return '{:.2f}'.format(mem_rss).zfill(5) + 'MB [MAX:{:.2f}'.format(self._statistics['mem_rss_max']).zfill(5) + 'MB]' + '/' + '{:.2f}'.format(mem_vms).zfill(5) + 'MB [MAX:{:.2f}'.format(
            self._statistics['mem_vms_max']).zfill(5) + 'MB]'

    def get_postfix(self, futures_length: int) -> dict[str, Any]:
        postfix = {
            'memory_usage': self.get_mem_usage(),
            'futures': futures_length,
        }
        if self._statistics['limits_reaches'] > 0:
            postfix['limit_reaches'] = self._statistics['limits_reaches']
        return postfix

    def extract_frame(self, frame_number: int) -> NumberedFrame:
        if frame_number > self.fc:
            raise EOutOfRange(frame_number, 0, self.fc)
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
