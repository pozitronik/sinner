import os
import queue
import sys
import threading
import time
from argparse import Namespace
from asyncio import Future
from concurrent.futures.thread import ThreadPoolExecutor
from enum import Enum
from typing import List, Callable

from tqdm import tqdm

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.Status import Status, Mood
from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.NoneHandler import NoneHandler
from sinner.helpers.FrameHelper import EmptyFrame, scale
from sinner.models.NumberedFrame import NumberedFrame
from sinner.models.PerfCounter import PerfCounter
from sinner.models.State import State
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.processors.frame.FrameExtractor import FrameExtractor
from sinner.typing import FramesList
from sinner.utilities import list_class_descendants, resolve_relative_path, suggest_execution_threads, suggest_temp_dir
from sinner.validators.AttributeLoader import Rules


class FrameMode(Enum):
    ALL = "All"
    AUTO = "Auto"
    FIXED = "Fixed"


class GUIModel(Status):
    # configuration variables
    frame_processor: List[str]
    _source_path: str
    _target_path: str
    execution_threads: int
    bootstrap: bool
    _prepare_frames: bool | None
    temp_dir: str
    _scale_quality: float  # the processed frame size scale from 0 to 1
    _player_buffer_length: int = 10  # frames needs to be rendered before player start
    _frame_mode: FrameMode

    parameters: Namespace

    # internal/external objects
    _processors: dict[str, BaseFrameProcessor]  # cached processors for gui [processor_name, processor]
    _target_handler: BaseFrameHandler | None = None  # the initial handler of the target file
    _player_canvas: BaseFramePlayer | None = None
    _previews: dict[int, FramesList] = {}  # position: [frame, caption]  # todo: make a component or modify FrameThumbnails
    _processed_frames_queue: queue.PriorityQueue[NumberedFrame]

    _progress_callback: Callable[[int], None] | None = None

    # player counters
    _frame_render_time: float = 0
    _fps: float = 1  # playing fps
    _frame_drop_reminder: float = 0
    _frame_wait_coefficient: float = 0

    # internal variables
    _is_target_frames_prepared: bool = False

    # threads
    _multi_process_frames_thread: threading.Thread | None = None
    _show_frames_thread: threading.Thread | None = None

    # threads control events
    _event_buffering: threading.Event = threading.Event()
    _event_displaying: threading.Event = threading.Event()
    _event_stop_player: threading.Event = threading.Event()  # the event to stop live player

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
                'parameter': {'quality', 'scale-quality'},
                'attribute': '_scale_quality',
                'default': 0.75,
                'help': 'Initial processing scale quality'
            },
            {
                'parameter': {'prepare-frames'},
                'attribute': '_prepare_frames',
                'default': None,
                'help': 'Extract target frames to files to make realtime player run smoother'
            },
            {
                'parameter': 'bootstrap',
                'attribute': 'bootstrap',
                'default': True,
                'help': 'Bootstrap frame processors on startup'
            },
            {
                'parameter': 'temp-dir',
                'default': lambda: suggest_temp_dir(self.temp_dir),
                'help': 'Select the directory for temporary files'
            },
            {
                'module_help': 'The GUI processing handler'
            }
        ]

    def __init__(self, parameters: Namespace):
        self._frame_mode: FrameMode = FrameMode.AUTO
        self.parameters = parameters
        super().__init__(parameters)
        self._processors = {}
        if self.bootstrap:
            self._processors = self.processors

        self._processed_frames_queue = queue.PriorityQueue()

        self._event_stop_player.set()
        # self._processing_thread_stop_event.set()

    def reload_parameters(self) -> None:
        self.clear_previews()
        self._target_handler = None
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
    def canvas(self) -> BaseFramePlayer | None:
        return self._player_canvas

    @canvas.setter
    def canvas(self, value: BaseFramePlayer | None) -> None:
        self._player_canvas = value

    @property
    def quality(self) -> int:
        return int(self._scale_quality * 100)

    @quality.setter
    def quality(self, value: int) -> None:
        self._scale_quality = value / 100

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

    @property
    def is_processors_loaded(self) -> bool:
        return self._processors != {}

    # returns list of all processed steps for a frame, starting from the original
    def get_frame_steps(self, frame_number: int, extractor_handler: BaseFrameHandler | None, processed: bool = False) -> FramesList:
        result: FramesList = []
        if extractor_handler is None:
            return result
        try:
            n_frame = extractor_handler.extract_frame(frame_number)
            result.append((n_frame.frame, 'Original'))  # add an original frame
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            return result
        if processed:  # return all processed frames
            for processor_name, processor in self.processors.items():
                frame = processor.process_frame(n_frame.frame)
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
        if self._target_handler is None:
            if self.target_path is None:
                self._target_handler = NoneHandler()
            else:
                self._target_handler = BatchProcessingCore.suggest_handler(self.target_path, self.parameters)
        return self._target_handler

    def get_previews(self, position: int) -> FramesList | None:
        return self._previews.get(position)

    def set_previews(self, position: int, previews: FramesList) -> None:
        self._previews[position] = previews

    def clear_previews(self) -> None:
        self._previews.clear()

    @property
    def player_is_playing(self) -> bool:
        return not self._event_stop_player.is_set()

    @property
    def frame_mode(self) -> FrameMode:
        return self._frame_mode

    @frame_mode.setter
    def frame_mode(self, value: str) -> None:
        frame_mode_mapping = {mode.value: mode for mode in FrameMode}
        if value in frame_mode_mapping:
            self._frame_mode = frame_mode_mapping[value]

    @property
    def frame_step(self) -> int:
        if self._frame_mode is FrameMode.ALL:
            return 1
        if self._frame_mode is FrameMode.AUTO:
            return self.calculate_framedrop() + 1
        if self._frame_mode is FrameMode.FIXED:
            return 3  # todo an editable value, I suppose

    def player_start(self, start_frame: int, canvas: BaseFramePlayer, progress_callback: Callable[[int], None] | None = None) -> None:
        if canvas:
            self.canvas = canvas
        if progress_callback:
            self.progress_callback = progress_callback
        if self._prepare_frames is not False and not self._is_target_frames_prepared:
            self._is_target_frames_prepared = self.prepare_frames()

        self._event_stop_player.clear()
        self.__start_buffering(start_frame)  # it also will start the player thread

    def player_stop(self, wait: bool = False, reload_frames: bool = False) -> None:
        self._event_stop_player.set()
        if wait:
            time.sleep(1)  # Allow time for the thread to respond
        self.__stop_display()
        self.__stop_buffering()
        if reload_frames:
            self._is_target_frames_prepared = False

    def __start_buffering(self, start_frame: int):
        if not self._event_buffering.is_set():
            self._multi_process_frames_thread = threading.Thread(target=self.multi_process_frames, name="multi_process_frames", kwargs={
                'start_frame': start_frame,
                'end_frame': self.frame_handler.fc
            })
            self._multi_process_frames_thread.daemon = True
            self._multi_process_frames_thread.start()
            self._event_buffering.set()

    def __stop_buffering(self):
        if self._event_buffering.is_set() and self._multi_process_frames_thread:
            self._multi_process_frames_thread.join(1)
            self._multi_process_frames_thread = None
            self._event_buffering.clear()

    def __start_display(self):
        if not self._event_displaying.is_set():
            self._show_frames_thread = threading.Thread(target=self.show_frames, name="show_frames")
            self._show_frames_thread.daemon = True
            self._show_frames_thread.start()
            self._event_displaying.set()

    def __stop_display(self):
        if self._event_displaying.is_set() and self._show_frames_thread:
            self._show_frames_thread.join(1)  # timeout is required to avoid problem with a wiggling navigation slider
            self._show_frames_thread = None
            self._event_displaying.clear()

    def multi_process_frames(self, start_frame: int, end_frame: int) -> None:
        def process_done(future_: Future[None]) -> None:
            futures.remove(future_)
            if processed_frames_count >= self._player_buffer_length and not self._event_displaying.is_set():
                self.__start_display()
            elif not self._event_displaying.is_set():
                self.update_status(f"Waiting to fill the buffer: {processed_frames_count} of {self._player_buffer_length}")

        self._processed_frames_queue = queue.PriorityQueue()  # clears the queue from the old frames
        futures: list[Future[None]] = []
        processed_frames_count = 0
        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:  # this adds processing operations into a queue
            while start_frame < end_frame:
                future: Future[None] = executor.submit(self.process_frame_to_queue, start_frame)
                future.add_done_callback(process_done)
                futures.append(future)
                processed_frames_count += 1
                start_frame += self.frame_step

                if len(futures) >= self.execution_threads:
                    futures[:1][0].result()
                    start_frame += self.frame_step

                if self._event_stop_player.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
            self._processed_frames_queue.put(NumberedFrame(sys.maxsize, EmptyFrame))

    def process_frame_to_queue(self, frame_index: int) -> None:
        if not self._event_stop_player.is_set():
            with PerfCounter() as frame_render_time:
                n_frame = self.frame_handler.extract_frame(frame_index)
                n_frame.frame = scale(n_frame.frame, self._scale_quality)
                for _, processor in self.processors.items():
                    n_frame.frame = processor.process_frame(n_frame.frame)
            n_frame.frame_time = frame_render_time.execution_time
            self._processed_frames_queue.put(n_frame)
            self.update_processing_fps(frame_render_time.execution_time)

    def show_frames(self) -> None:
        _frame_time = 1 / self.frame_handler.fps
        timer = 0
        if self.canvas:
            while not self._event_stop_player.is_set():  # todo: need two different events, one for the render thread, and other one for the player
                try:
                    n_frame = self._processed_frames_queue.get(block=False)
                    if n_frame.number == sys.maxsize:  # use as the stop marker
                        self._event_stop_player.set()
                        continue

                    fps = 1 / n_frame.frame_time
                    expected_frame_time = _frame_time * (self.frame_handler.fps / fps)

                    expected_timer = time.perf_counter()
                    self.canvas.show_frame_wait(n_frame.frame, duration=expected_frame_time)
                    # self.update_status(f"Frame time: {time.perf_counter() - expected_timer}, expected: {expected_frame_time}")
                    timer += expected_frame_time
                    if self.progress_callback:
                        self.progress_callback(n_frame.number)
                except queue.Empty:
                    # self.update_status("Waiting for a frame")
                    continue
            self.update_status(f"Playing time: {timer}", mood=Mood.BAD)

    # method computes the current processing fps based on the median time of all processed frames timings
    def update_processing_fps(self, frame_render_ns: float) -> None:
        self._frame_render_time = (self._frame_render_time + frame_render_ns) / self.execution_threads
        self._fps = 1 / self._frame_render_time

    # return the count of the skipped frames for the next iteration
    def calculate_framedrop(self) -> int:
        if self._fps >= self.frame_handler.fps:  # render is faster than video
            frame_drop = 0  # no frame skip
        else:  # render is slower than video
            self._frame_wait_coefficient = ((self.frame_handler.fps / self._fps) + self._frame_drop_reminder)
            frame_drop = int(self._frame_wait_coefficient) - 1
            self._frame_drop_reminder = self._frame_wait_coefficient % 1  # do not lose reminder, use it in the next iteration
            # self.update_status(f"fps_coefficient: {fps_coefficient}, Framedrop: {frame_drop}, Reminder: {self._frame_drop_reminder}")
        return frame_drop

    def prepare_frames(self) -> bool:
        frame_extractor = FrameExtractor(self.parameters)
        state = State(parameters=self.parameters, target_path=self._target_path, temp_dir=self.temp_dir, frames_count=self.frame_handler.fc, processor_name=frame_extractor.__class__.__name__)
        frame_extractor.configure_state(state)
        state_is_finished = state.is_finished

        if state_is_finished:
            self.update_status(f'Extracting frames already done ({state.processed_frames_count}/{state.frames_count})')
        elif self._prepare_frames is True:
            if state.is_started:
                self.update_status(f'Temp resources for this target already exists with {state.processed_frames_count} frames extracted, continue with {state.processor_name}')
            with tqdm(
                    total=state.frames_count,
                    desc=state.processor_name, unit='frame',
                    dynamic_ncols=True,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
                    initial=state.processed_frames_count,
            ) as progress:
                self.frame_handler.current_frame_index = state.processed_frames_count
                for frame_num in self.frame_handler:
                    n_frame = self.frame_handler.extract_frame(frame_num)
                    state.save_temp_frame(n_frame)
                    progress.update()

        frame_extractor.release_resources()
        if state_is_finished:
            self._target_handler = DirectoryHandler(state.path, self.parameters, self.frame_handler.fps, self.frame_handler.fc, self.frame_handler.resolution)
        return state_is_finished
