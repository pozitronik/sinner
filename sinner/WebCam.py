import queue
import sys
import threading
import time
from argparse import Namespace
from typing import List

import cv2
from cv2 import VideoCapture
from pyvirtualcam import Camera

from sinner.Status import Status, Mood
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import list_class_descendants, resolve_relative_path, is_image
from sinner.validators.AttributeLoader import Rules


class ImageCamera(VideoCapture):
    _frame: Frame

    def __init__(self, image: str, width: int, height: int):
        super().__init__()
        self._frame = CV2VideoHandler.read_image(image)
        self._frame = cv2.resize(self._frame, (width, height))

    def read(self, image: cv2.typing.MatLike | None = None) -> tuple[bool, Frame]:
        return True, self._frame


class NoDevice(Camera):
    def send(self, frame: Frame) -> None:
        return None

    def sleep_until_next_frame(self) -> None:
        return None


class WebCam(Status):
    emoji: str = '🤳'

    stop: bool = False

    frame_processor: List[str]
    preview: bool
    input_device: int | str
    output_device: str | None
    width: int
    height: int
    fps: int
    print_fps: bool
    auto_restart: bool

    _camera_input: VideoCapture
    _processors: List[BaseFrameProcessor] = []
    _device: Camera
    _fps_delay: float

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'frame-processor', 'processor', 'processors'},
                'attribute': 'frame_processor',
                'default': ['FaceSwapper'],
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor'),
                'help': 'The set of frame processors to handle the camera input'
            },
            {
                'parameter': 'preview',
                'default': True,
                'help': 'Show resulting picture in a separate window'
            },
            {
                'parameter': ['input', 'input-device'],
                'attribute': 'input_device',
                'default': 0,
                'help': 'Input camera index (ignore, if you have one camera). Pass a path to an image file to use it as input.'
            },
            {
                'parameter': ['device', 'output-device'],
                'default': None,
                'choices': self.list_available_output_devices(),
                'attribute': 'output_device',
                'help': 'Output device name (e.g. virtual camera device to use), ignore to the first available device or use "no" to skip output'
            },
            {
                'parameter': 'width',
                'default': 640,
                'help': 'The output device resolution width'
            },
            {
                'parameter': 'height',
                'default': 480,
                'help': 'The output device resolution height'
            },
            {
                'parameter': 'fps',
                'default': 30,
                'help': 'The output device fps'
            },
            {
                'parameter': 'print-fps',
                'default': False,
                'help': 'Print frame rate every second'
            },
            {
                'parameter': ['auto-restart', 'restart'],
                'default': True,
                'help': 'Try to restart input camera on error (may help with buggy drivers/hardware)'
            },
            {
                'module_help': 'The virtual camera module'
            }
        ]

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        super().__init__(parameters)
        self.open_camera()
        if self.output_device == 'no':  # creates a dummy output
            self._device = NoDevice(width=self.width, height=self.height, fps=self.fps)
        else:
            self._device = Camera(width=self.width, height=self.height, fps=self.fps, device=self.output_device, backend=self.output_device, print_fps=self.print_fps)
            self.update_status(f"Virtual device camera is created as {self.output_device} with {self.width}x{self.height}@{self.fps}fps output")

        for processor_name in self.frame_processor:
            self._processors.append(BaseFrameProcessor.create(processor_name, self.parameters))
        self._fps_delay = 1 / self.fps

    @staticmethod
    def preview_frames(frame_queue: queue.Queue) -> None:
        while True:
            frame = frame_queue.get()
            cv2.imshow('Frame', frame)
            cv2.waitKey(1)

    def run(self) -> None:
        if self.preview:
            frame_queue = queue.Queue()
            display_thread = threading.Thread(target=self.preview_frames, args=(frame_queue,))
            display_thread.start()
        with self._device as camera:
            while not self.stop:
                frame_start_time = time.perf_counter()
                ret, frame = self._camera_input.read()
                if not ret:
                    self.update_status(f"Error reading input from camera", mood=Mood.BAD)
                    if self.auto_restart:
                        self.update_status(f"Reopening camera device")
                        self._camera_input.release()
                        self.open_camera()
                    continue
                for processor in self._processors:
                    frame = processor.process_frame(frame)
                if self.preview:
                    frame_queue.put(frame)

                camera.send(frame)
                camera.sleep_until_next_frame()
                frame_end_time = time.perf_counter()
                frame_render_time = frame_end_time - frame_start_time
                if frame_render_time < self._fps_delay:
                    time.sleep(self._fps_delay - frame_render_time)
                self.update_status(f"Real fps is {(1 / frame_render_time):.2f}", position=(-1, 0))
        if self.preview:
            display_thread.join()

    def open_camera(self) -> VideoCapture:
        if isinstance(self.input_device, str) and is_image(self.input_device):
            self._camera_input = ImageCamera(self.input_device, self.width, self.height)
            self.update_status(f"Using image {self.input_device} as camera input")
            return self._camera_input

        self._camera_input = cv2.VideoCapture(self.input_device)
        if not self._camera_input.isOpened():
            raise Exception(f"Error opening camera {self.input_device}")
        self.update_status(f"Camera input is opened at device={self.input_device}")
        return self._camera_input

    @staticmethod
    def list_available_output_devices() -> List[str]:
        devices: List[str] = ['no']
        if sys.platform == 'linux':
            devices.append('v4l2loopback')
        if sys.platform == 'win32':
            devices.append('unitycapture')
        if sys.platform == 'Darwin' or sys.platform == 'win32':
            devices.append('obs')
        return devices
