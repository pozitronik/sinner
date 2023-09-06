import sys
from argparse import Namespace
from typing import List

import cv2
from cv2 import VideoCapture
from pyvirtualcam import Camera

from sinner.Status import Status
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.utilities import list_class_descendants, resolve_relative_path
from sinner.validators.AttributeLoader import Rules


class WebCam(Status):
    emoji: str = '🤳'

    stop: bool = False

    frame_processor: List[str]
    preview: bool
    input_device: int
    output_device: str | None
    width: int
    height: int
    fps: int
    print_fps: bool

    _camera_input: VideoCapture
    _processors: List[BaseFrameProcessor] = []
    _device: Camera

    def rules(self) -> Rules:
        return [
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
                'help': 'Input camera index (ignore, if you have one camera)'
            },
            {
                'parameter': ['output', 'output-device'],
                'default': None,
                'choices': self.list_available_output_devices(),
                'attribute': 'output_device',
                'help': 'Output device name (e.g. virtual camera device to use), ignore to the first available device'
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
                'module_help': 'The virtual camera module'
            }
        ]

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        super().__init__(parameters)
        self._camera_input = self.open_camera()
        self.update_status("Camera input is opened")

        self._device = Camera(width=self.width, height=self.height, fps=self.fps, device=self.output_device, backend=self.output_device, print_fps=self.print_fps)
        self.update_status(f"Virtual device camera is created as {self.output_device} with {self.width}x{self.height}@{self.fps}fps output")

        for processor_name in self.frame_processor:
            self._processors.append(BaseFrameProcessor.create(processor_name, self.parameters))

    def run(self):
        with self._device as camera:
            while not self.stop:
                ret, frame = self._camera_input.read()
                if not ret:
                    raise Exception(f"Error reading frame from camera")
                for processor in self._processors:
                    frame = processor.process_frame(frame)
                camera.send(frame)
                camera.sleep_until_next_frame()

    def open_camera(self) -> VideoCapture:
        cap = cv2.VideoCapture(self.input_device)
        if not cap.isOpened():
            raise Exception(f"Error opening camera {self.input_device}")
        return cap

    @staticmethod
    def list_available_output_devices() -> List[str]:
        devices: List[str] = []
        if sys.platform == 'linux':
            devices.append('v4l2loopback')
        if sys.platform == 'win32':
            devices.append('unitycapture')
        if sys.platform == 'Darwin' or sys.platform == 'win32':
            devices.append('obs')
        return devices
