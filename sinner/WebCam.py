import time
from argparse import Namespace

import cv2
from cv2 import VideoCapture
from pyvirtualcam import Camera

from sinner.Status import Status
from sinner.processors.frame.FaceEnhancer import FaceEnhancer
from sinner.processors.frame.FaceSwapper import FaceSwapper


class WebCam(Status):
    stop: bool = False
    face_swapper: FaceSwapper

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        super().__init__(parameters)
        self.face_swapper = FaceSwapper(parameters)
        # self.face_enhancer = FaceEnhancer(parameters)

    def run(self):
        input_camera = self.open_camera()
        with Camera(width=640, height=480, fps=24) as camera:
            while not self.stop:
                ret, frame = input_camera.read()

                if not ret:
                    raise Exception(f"Error reading frame from camera")

                frame = self.face_swapper.process_frame(frame)
                # current_height, current_width = frame.shape[:2]
                # frame = cv2.resize(frame, (320, 240))
                # frame = self.face_enhancer.process_frame(frame)

                camera.send(frame)
                camera.sleep_until_next_frame()

    @staticmethod
    def open_camera() -> VideoCapture:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise Exception("Error opening frame file")
        return cap
