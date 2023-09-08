import cv2

from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import is_int, is_float


class FrameResizer(BaseFrameProcessor):
    emoji: str = '🔍'

    scale: float
    height: int
    width: int
    height_max: int
    width_max: int
    height_min: int
    width_min: int

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'scale'},
                'attribute': 'scale',
                'default': 1,
                'valid': lambda attribute, value: is_float(value),
                'help': 'Select frame resize scale'
            },
            {
                'parameter': {'height'},
                'attribute': 'height',
                'default': None,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Select resize height'
            },
            {
                'parameter': {'width'},
                'attribute': 'width',
                'default': None,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Select resize width'
            },
            {
                'parameter': {'height-max'},
                'attribute': 'height_max',
                'default': None,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Select maximal allowed height'
            },
            {
                'parameter': {'width-max'},
                'attribute': 'width_max',
                'default': None,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Select maximal allowed width'
            },
            {
                'parameter': {'height-min'},
                'attribute': 'height_min',
                'default': None,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Select minimal allowed height'
            },
            {
                'parameter': {'width-min'},
                'attribute': 'width_min',
                'default': None,
                'valid': lambda attribute, value: is_int(value),
                'help': 'Select minimal allowed width'
            },
            {
                'module_help': 'This module changes images resolution'
            }
        ]

    def calculate_scale(self, frame: Frame) -> float:
        current_height, current_width = frame.shape[:2]
        if self.height_max is not None and current_height > self.height_max and (self.height is None or self.height > self.height_max):
            self.height = self.height_max
        if self.width_max is not None and current_width > self.width_max and (self.width is None or self.width > self.width_max):
            self.width = self.width_max
        if self.height_min is not None and current_height < self.height_min and (self.height is None or self.height < self.height_min):
            self.height = self.height_min
        if self.width_min is not None and current_width < self.width_min and (self.width is None or self.width < self.width_min):
            self.width = self.width_min

        if self.height is not None:
            return self.height / current_height
        elif self.width is not None:
            return self.width / current_width
        else:
            return self.scale

    def process_frame(self, frame: Frame) -> Frame:
        current_height, current_width = frame.shape[:2]
        scale = self.calculate_scale(frame)
        return cv2.resize(frame, (int(current_width * scale), int(current_height * scale)))
