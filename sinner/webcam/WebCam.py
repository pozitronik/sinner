import queue
import threading
import time
from argparse import Namespace
from tkinter import Canvas, NW
from typing import List
import tkinter as tk
import cv2
from PIL import Image, ImageTk
from cv2 import VideoCapture
from psutil import WINDOWS, LINUX, MACOS
from pyvirtualcam import Camera

from sinner.Status import Status, Mood
from sinner.models.PerfCounter import PerfCounter
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import list_class_descendants, resolve_relative_path, is_image, is_video
from sinner.validators.AttributeLoader import Rules
from sinner.webcam.ImageCamera import ImageCamera
from sinner.webcam.NoDevice import NoDevice
from sinner.webcam.VideoCamera import VideoCamera


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

    PreviewWindow: tk.Tk
    canvas: Canvas
    _processing_thread: threading.Thread
    _frames_queue: queue.Queue[Frame]

    _frame_render_time: float = 0

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'frame-processor', 'processor', 'processors'},
                'attribute': 'frame_processor',
                'default': ['FaceSwapper'],
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('../processors/frame'), 'BaseFrameProcessor'),
                'help': 'The set of frame processors to handle the camera input'
            },
            {
                'parameter': 'preview',
                'default': True,
                'help': 'Show virtual camera preview in a separate window'
            },
            {
                'parameter': ['input', 'input-device'],
                'attribute': 'input_device',
                'default': 0,
                'help': 'Input camera index (ignore, if you have only one camera device). Pass a path to an image/video file to use it as the input'
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

    @staticmethod
    def list_available_output_devices() -> List[str]:
        devices: List[str] = ['no']
        if LINUX:
            devices.append('v4l2loopback')
        if WINDOWS:
            devices.append('unitycapture')
        if MACOS or WINDOWS:
            devices.append('obs')
        return devices

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        super().__init__(parameters)
        self.open_camera()
        if self.output_device == 'no':  # creates a dummy output
            self._device = NoDevice(width=self.width, height=self.height, fps=self.fps)
        else:
            self._device = Camera(width=self.width, height=self.height, fps=self.fps, device=self.output_device, backend=self.output_device, print_fps=self.print_fps)
            self.update_status(f"Virtual device camera is created as {self.output_device} with {self.width}x{self.height}@{self.fps}fps output")

        self._frames_queue = queue.Queue()

        for processor_name in self.frame_processor:
            self._processors.append(BaseFrameProcessor.create(processor_name, self.parameters))
        self._fps_delay = 1 / self.fps

    def open_camera(self) -> VideoCapture:
        if isinstance(self.input_device, str):
            if is_image(self.input_device):
                self._camera_input = ImageCamera(self.input_device, self.width, self.height)
                self.update_status(f"Using image {self.input_device} as camera input")
                return self._camera_input
            if is_video(self.input_device):
                self._camera_input = VideoCamera(self.input_device, self._frame_render_time, self.width, self.height)
                self.update_status(f"Using video file {self.input_device} as camera input")
                return self._camera_input

        self._camera_input = cv2.VideoCapture(self.input_device)
        if not self._camera_input.isOpened():
            raise Exception(f"Error opening camera {self.input_device}")
        self.update_status(f"Camera input is opened at device={self.input_device}")
        return self._camera_input

    def process(self) -> None:
        with self._device as camera:
            while not self.stop:
                with PerfCounter() as render_time:
                    ret, frame = self._camera_input.read()
                    if not ret:
                        self.update_status("Error reading input from camera", mood=Mood.BAD)
                        if self.auto_restart:
                            self.update_status("Reopening camera device")
                            self._camera_input.release()
                            self.open_camera()
                        continue
                    for processor in self._processors:
                        frame = processor.process_frame(frame)
                    if self.preview:
                        self._frames_queue.put(frame)

                    camera.send(frame)
                    camera.sleep_until_next_frame()
                self._frame_render_time = render_time.execution_time
                if self._frame_render_time < self._fps_delay:
                    time.sleep(self._fps_delay - self._frame_render_time)
                self.update_status(f"Real fps is {(1 / self._frame_render_time):.2f}", position=(-1, 0))
                if hasattr(self._camera_input, '_last_frame_render_time'):
                    setattr(self._camera_input, '_last_frame_render_time', self._frame_render_time)

    def run(self) -> None:
        if self.preview:
            self.show_preview()

    def start_processing_thread(self) -> None:
        self._processing_thread = threading.Thread(target=self.process)
        self._processing_thread.daemon = True
        self._processing_thread.start()

    def preview_frames(self) -> None:
        try:
            frame = self._frames_queue.get(timeout=1)
            photo = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=photo, anchor=NW)
            self.canvas.photo = photo  # type: ignore[attr-defined]
        except queue.Empty:
            pass
        self.PreviewWindow.after(int(self._frame_render_time * 1000), self.preview_frames)

    def show_preview(self) -> None:
        self.PreviewWindow = tk.Tk()
        self.PreviewWindow.title('Camera Preview')
        self.PreviewWindow.resizable(width=True, height=True)
        self.canvas = Canvas(self.PreviewWindow, width=self.width, height=self.height)
        self.canvas.pack(fill='both', expand=True)
        self.start_processing_thread()
        self.PreviewWindow.after(int(self._frame_render_time * 1000), self.preview_frames)
        self.PreviewWindow.mainloop()
