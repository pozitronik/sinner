import os
import queue
import threading
import time
from argparse import Namespace
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List

import cv2

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.Status import Status, Mood
from sinner.gui.controls.PreviewCanvas import PreviewCanvas
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame, FramesList
from sinner.utilities import list_class_descendants, resolve_relative_path
from sinner.validators.AttributeLoader import Rules, AttributeLoader


class GUIModel(Status):
    frame_processor: List[str]
    _source_path: str
    _target_path: str

    parameters: Namespace
    _processors: dict[str, BaseFrameProcessor]  # cached processors for gui [processor_name, processor]
    preview_handlers: dict[str, BaseFrameHandler]  # cached handlers for gui

    _extractor_handler: BaseFrameHandler | None = None
    _previews: dict[int, FramesList] = {}  # position: [frame, caption]  # todo: make a component or modify FrameThumbnails
    _current_frame: Frame | None
    _scale_quality: float  # the processed frame size scale from 0 to 1
    _processing_thread: threading.Thread
    _viewing_thread: threading.Thread
    _frames_queue: queue.PriorityQueue[tuple[int, Frame]]
    _frame_wait_time: float = 0
    _is_playing: bool = False
    _fps: float  # playing fps

    frame_processor: List[str]

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'frame-processor', 'processor', 'processors'},
                'attribute': 'frame_processor',
                'default': ['FaceSwapper'],
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('../processors/frame'), 'BaseFrameProcessor'),
                'help': 'The set of frame processors to handle the target'
            },
            {
                'parameter': {'source', 'source-path'},
                'attribute': '_source_path'
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': '_target_path'
            },
            {
                'module_help': 'The GUI processing handler'
            }
        ]

    def __init__(self, parameters: Namespace):
        self._scale_quality = 0.3
        self.parameters = parameters
        super().__init__(parameters)
        self._processors = {}
        self._frames_queue = queue.PriorityQueue()

    def reload_parameters(self) -> None:
        self.clear_previews()
        self._extractor_handler = None
        super().__init__(self.parameters)
        for _, processor in self.processors.items():
            processor.load(self.parameters)

    @property
    def source_path(self) -> str | None:
        return self._source_path

    @source_path.setter
    def source_path(self, value: str | None) -> None:
        self.parameters.source = value
        self.reload_parameters()

    @property
    def target_path(self) -> str | None:
        return self._target_path

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        self.parameters.target = value
        self.reload_parameters()

    @property
    def source_dir(self) -> str:
        return os.path.dirname(self._source_path)

    @property
    def target_dir(self) -> str:
        return os.path.dirname(self._target_path)

    @property
    def processors(self) -> dict[str, BaseFrameProcessor]:
        try:
            for processor_name in self.frame_processor:
                if processor_name not in self._processors:
                    self._processors[processor_name] = BaseFrameProcessor.create(processor_name, self.parameters)
        except Exception as exception:  # skip, if parameters is not enough for processor
            self.update_status(message=str(exception), mood=Mood.BAD)
            pass
        return self._processors

    # returns list of all processed steps for a frame, starting from the original
    def get_frame_steps(self, frame_number: int, extractor_handler: BaseFrameHandler, processed: bool = False) -> FramesList:
        result: FramesList = []
        try:
            _, frame, _ = extractor_handler.extract_frame(frame_number)
            result.append((frame, 'Original'))  # add an original frame
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            return result
        if processed:  # return all processed frames
            for processor_name, processor in self.processors.items():
                frame = processor.process_frame(frame)
                result.append((frame, processor_name))
        return result

    def get_frames(self, frame_number: int = 0, processed: bool = False) -> FramesList:
        saved_frames = self.get_previews(frame_number)
        if saved_frames:  # frame already in the cache
            return saved_frames
        frame_steps = self.get_frame_steps(frame_number, self.frame_handler, processed)
        if processed:
            self.set_previews(frame_number, frame_steps)  # cache, if processing has requested
        return frame_steps

    @property
    def frame_handler(self) -> BaseFrameHandler:
        if self._extractor_handler is None:
            self._extractor_handler = BatchProcessingCore.suggest_handler(self.target_path, self.parameters)
        return self._extractor_handler

    def get_previews(self, position: int) -> FramesList | None:
        return self._previews.get(position)

    def set_previews(self, position: int, previews: FramesList) -> None:
        self._previews[position] = previews

    def clear_previews(self):
        self._previews.clear()

    def play(self, start_from: int, canvas: PreviewCanvas) -> None:
        self._is_playing = not self._is_playing
        if not self._is_playing:
            self._processing_thread.join()
            self._viewing_thread.join()
        else:
            self._processing_thread = threading.Thread(target=self.multi_process_frames, kwargs={'start_from': start_from})
            self._processing_thread.daemon = True
            self._processing_thread.start()

            self._viewing_thread = threading.Thread(target=self.show_frames, kwargs={'canvas': canvas})
            self._viewing_thread.daemon = True
            self._viewing_thread.start()

    def multi_process_frames(self, start_from: int = 0) -> None:
        self.frame_handler.current_frame_index = start_from
        with ThreadPoolExecutor(max_workers=2) as executor:
            while self.frame_handler.current_frame_index < self.frame_handler.fc:
                if not self._is_playing:
                    break
                executor.submit(self.process_frame_to_queue, self.frame_handler.current_frame_index)
                self.frame_handler.current_frame_index += 1

    def process_frame_to_queue(self, frame_index: int) -> None:
        index, frame, _ = self.frame_handler.extract_frame(frame_index)
        frame = self.resize_frame(frame, self._scale_quality)
        for _, processor in self.processors.items():
            frame = processor.process_frame(frame)
        self._frames_queue.put((index, frame))  # todo: queue needs to be cleared on source/target reload

    @staticmethod
    def resize_frame(frame: Frame, scale: float = 0.2) -> Frame:
        current_height, current_width = frame.shape[:2]
        return cv2.resize(frame, (int(current_width * scale), int(current_height * scale)))

    def show_frames(self, canvas: PreviewCanvas) -> None:
        if self._is_playing:
            frame_wait_start = time.perf_counter()
            index, frame = self._frames_queue.get()
            frame_wait_end = time.perf_counter()
            self._frame_wait_time = frame_wait_end - frame_wait_start
            canvas.show_frame(frame)
            # self.NavigateSlider.set(index)
            # self._fps = 1 / self._frame_wait_time
            # self.current_position.set(f'{int(self.NavigateSlider.get())}/{self.NavigateSlider.cget("to")}')
            # self.update_status(f"index: {index}, fps: {self._fps}, qsize: {self._frames_queue.qsize()}, frame: {frame.shape}")
            canvas.after(int(self._frame_wait_time * 100), self.show_frames, canvas)
