import os
import queue
import threading
import time
from argparse import Namespace
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Callable

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.Status import Status, Mood
from sinner.gui.controls.PreviewCanvas import PreviewCanvas
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame, FramesList
from sinner.utilities import list_class_descendants, resolve_relative_path, suggest_execution_threads, resize_frame
from sinner.validators.AttributeLoader import Rules


class GUIModel(Status):
    frame_processor: List[str]
    _source_path: str
    _target_path: str
    execution_threads: int

    parameters: Namespace
    _processors: dict[str, BaseFrameProcessor]  # cached processors for gui [processor_name, processor]
    preview_handlers: dict[str, BaseFrameHandler]  # cached handlers for gui

    _extractor_handler: BaseFrameHandler | None = None
    _previews: dict[int, FramesList] = {}  # position: [frame, caption]  # todo: make a component or modify FrameThumbnails
    _current_frame: Frame | None
    _scale_quality: float  # the processed frame size scale from 0 to 1
    _multi_process_frames_thread: threading.Thread | None = None
    _show_frames_thread: threading.Thread | None = None

    _player_stop_event: threading.Event  # the event to stop live player
    _frames_queue: queue.PriorityQueue[tuple[int, Frame]]
    _frame_render_time: float = 0
    _fps: float = 1  # playing fps
    _player_canvas: PreviewCanvas | None = None
    _progress_callback: Callable[[int], None] | None = None

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
                'parameter': 'execution-threads',
                'type': int,
                'default': suggest_execution_threads(),
                'help': 'The count of simultaneous processing threads'
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

        self._scale_quality = 0.4
        self.parameters = parameters
        super().__init__(parameters)
        self._processors = {}
        self._player_stop_event = threading.Event()
        self.processing_thread_stop_event = threading.Event()
        self.viewing_thread_stop_event = threading.Event()
        self._player_stop_event.set()

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
    def source_dir(self) -> str | None:
        return os.path.dirname(self._source_path) if self._source_path else None

    @property
    def target_dir(self) -> str | None:
        return os.path.dirname(self._target_path) if self._target_path else None

    @property
    def canvas(self) -> PreviewCanvas | None:
        return self._player_canvas

    @canvas.setter
    def canvas(self, value: PreviewCanvas | None) -> None:
        self._player_canvas = value

    @property
    def progress_callback(self) -> Callable[[int], None] | None:
        return self._progress_callback

    @progress_callback.setter
    def progress_callback(self, value: Callable[[int], None] | None = None) -> None:
        self._progress_callback = value

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
        if extractor_handler is None:
            return result
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
    def frame_handler(self) -> BaseFrameHandler | None:
        if self.target_path is None:
            return None
        if self._extractor_handler is None:
            self._extractor_handler = BatchProcessingCore.suggest_handler(self.target_path, self.parameters)
        return self._extractor_handler

    def get_previews(self, position: int) -> FramesList | None:
        return self._previews.get(position)

    def set_previews(self, position: int, previews: FramesList) -> None:
        self._previews[position] = previews

    def clear_previews(self):
        self._previews.clear()

    @property
    def player_is_playing(self) -> bool:
        return not self._player_stop_event.is_set()

    def player_start(self, start_frame: int, frame_step: int = 1, canvas: PreviewCanvas | None = None, progress_callback: Callable[[int], None] | None = None) -> None:
        if canvas:
            self.canvas = canvas
        if progress_callback:
            self.progress_callback = progress_callback
        self._player_stop_event.clear()
        self._multi_process_frames_thread = threading.Thread(target=self.multi_process_frames, kwargs={
            'start_frame': start_frame,
            'end_frame': self.frame_handler.fc,
            'frame_step': frame_step
        })
        self._multi_process_frames_thread.daemon = False
        self._multi_process_frames_thread.start()

        self._show_frames_thread = threading.Thread(target=self.show_frames)
        self._show_frames_thread.daemon = False
        self._show_frames_thread.start()

    def player_stop(self, wait: bool = False) -> None:
        self._player_stop_event.set()
        if wait:
            time.sleep(1)  # Allow time for the thread to respond
        if self._multi_process_frames_thread:
            self._multi_process_frames_thread.join(1)
        if self._show_frames_thread:
            self._show_frames_thread.join(1)  # timeout is required to avoid problem with a wiggling navigation slider

    def multi_process_frames(self, start_frame: int, end_frame: int, frame_step: int = 1) -> None:
        self._frames_queue = queue.PriorityQueue()  # clears the queue from the old frames
        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:  # this adds processing operations into a queue
            while start_frame < end_frame:
                executor.submit(self.process_frame_to_queue, start_frame)
                start_frame += 5
                if self._player_stop_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    def process_frame_to_queue(self, frame_index: int) -> None:
        if not self._player_stop_event.is_set():
            frame_start_time = time.perf_counter()
            index, frame, _ = self.frame_handler.extract_frame(frame_index)
            frame = resize_frame(frame, self._scale_quality)
            for _, processor in self.processors.items():
                frame = processor.process_frame(frame)
            self._frames_queue.put((index, frame))
            frame_render_time = time.perf_counter() - frame_start_time
            self.update_processing_fps(frame_render_time)

    def show_frames(self) -> None:
        _frame_wait_time = 0.1 / self.frame_handler.fps
        if self.canvas:
            while not self._player_stop_event.is_set():
                try:
                    index, frame = self._frames_queue.get(block=False)  # non-blocking reading, raises queue.Empty if no frames there
                    self.canvas.show_frame(frame)
                    if self.progress_callback:
                        self.progress_callback(index)
                except queue.Empty:  # there are no frames processed
                    if not self._player_stop_event.is_set():
                        time.sleep(_frame_wait_time)
                if not self._player_stop_event.is_set():
                    time.sleep(_frame_wait_time)

    # method computes the current processing fps based on the median time of all processed frames timings
    def update_processing_fps(self, frame_render_ns: float):
        self._frame_render_time = (self._frame_render_time + frame_render_ns) / self.execution_threads
        self._fps = 1 / self._frame_render_time
        self.update_status(f"frt:{self._frame_render_time}, fps: {self._fps}, queue: {self._frames_queue.qsize()}")
