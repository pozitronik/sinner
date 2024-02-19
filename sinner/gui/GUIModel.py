import os
import threading
import time
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor, Future
from tkinter import IntVar
from typing import List, Callable, Any

from tqdm import tqdm

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.Status import Status, Mood
from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.gui.controls.FramePlayer.PygameFramePlayer import PygameFramePlayer
from sinner.gui.controls.ProgressBarManager import ProgressBarManager
from sinner.handlers.frame.EOutOfRange import EOutOfRange
from sinner.models.FrameTimeLine import FrameTimeLine
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.NoneHandler import NoneHandler
from sinner.helpers.FrameHelper import scale
from sinner.models.Event import Event
from sinner.models.PerfCounter import PerfCounter
from sinner.models.State import State
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.processors.frame.FrameExtractor import FrameExtractor
from sinner.typing import FramesList
from sinner.utilities import list_class_descendants, resolve_relative_path, suggest_execution_threads, suggest_temp_dir, iteration_mean, seconds_to_hmsms, normalize_path, get_mem_usage
from sinner.validators.AttributeLoader import Rules

BUFFERING_PROGRESS_NAME = "Buffering"
EXTRACTING_PROGRESS_NAME = "Extracting"


class GUIModel(Status):
    # configuration variables
    frame_processor: List[str]
    _source_path: str
    _target_path: str
    temp_dir: str
    execution_threads: int
    bootstrap_processors: bool  # bootstrap_processors processors on startup
    _prepare_frames: bool  # True: always extract and use, False: newer extract nor use, Null: newer extract, use if exists. Note: attribute can't be typed as bool | None due to AttributeLoader limitations
    _initial_frame_buffer_length: int  # frames needs to be rendered before player start. Also used to determine initial frame drop
    _scale_quality: float  # the processed frame size scale from 0 to 1

    parameters: Namespace

    # internal/external objects
    TimeLine: FrameTimeLine
    Player: BaseFramePlayer
    ProgressBarsManager: ProgressBarManager

    _processors: dict[str, BaseFrameProcessor]  # cached processors for gui [processor_name, processor]
    _target_handler: BaseFrameHandler | None = None  # the initial handler of the target file
    _positionVar: IntVar | None = None

    _previews: dict[int, FramesList] = {}  # position: [frame, caption]  # todo: make a component or modify FrameThumbnails

    _status: Callable[[str, str], Any]

    # player counters
    _buffered_frames_count: int = 0  # counter of buffered frames
    _processed_frames_count: int = 0  # the overall count of processed frames
    _shown_frames_count: int = 0  # the overall count of shown frames
    _current_framedrop: int = 0  # the current value of frames skipped on each processing iteration
    _framedrop_delta: int | None = None  # the required index of preprocessed frames
    _framedrop: int = 0  # the manual value of dropped frames

    _process_fps: float = 0

    # internal variables
    _is_target_frames_extracted: bool = False

    # threads
    _process_frames_thread: threading.Thread | None = None
    _show_frames_thread: threading.Thread | None = None

    # threads control events
    _event_buffering: Event  # the flag control to start/stop processed frames buffering thread
    _event_playback: Event  # the flag control to start/stop processed frames playback thread

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
                'parameter': ['bootstrap_processors', 'bootstrap'],
                'attribute': 'bootstrap_processors',
                'default': True,
                'help': 'Bootstrap frame processors on startup'
            },
            {
                'parameter': 'initial_frame_buffer_length',
                'attribute': '_initial_frame_buffer_length',
                'default': lambda: int(self.frame_handler.fps * 2),  # two seconds
                'help': 'The count of preprocessed frames'
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

    def __init__(self, parameters: Namespace, pb_control: ProgressBarManager, status_callback: Callable[[str, str], Any]):
        self.parameters = parameters
        super().__init__(parameters)
        self._processors = {}
        if self.bootstrap_processors:
            self._processors = self.processors

        self.TimeLine = FrameTimeLine(source_name=self._source_path, target_name=self.target_path, temp_dir=self.temp_dir, end_frame=self.frame_handler.fc)
        self.Player = PygameFramePlayer(width=self.frame_handler.resolution[0], height=self.frame_handler.resolution[1], caption='sinner player')
        self.ProgressBarsManager = pb_control
        self._status = status_callback
        self._status("Time position", seconds_to_hmsms(0))
        self._status("Frame drop", "0")

        self._event_buffering = Event(on_set_callback=lambda: self.update_status("BUFFERING: ON"), on_clear_callback=lambda: self.update_status("BUFFERING: OFF"))
        self._event_playback = Event(on_set_callback=lambda: self.update_status("PLAYBACK: ON"), on_clear_callback=lambda: self.update_status("PLAYBACK: OFF"))

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

        if self.player_is_started:  # todo: возможно оно и не надо
            self.player_stop()
            self.player_start(start_frame=self.TimeLine.last_requested_index, buffer_wait=False)
        else:
            self.update_preview()

    @property
    def target_path(self) -> str | None:
        return self._target_path

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        self.parameters.target = value
        self.reload_parameters()
        self.Player.clear()
        if self.player_is_started:
            self.player_stop(reload_frames=True)
            self.position.set(1)
            self.player_start(start_frame=1)
        else:
            self._is_target_frames_extracted = False
            self.update_preview()

    @property
    def source_dir(self) -> str | None:
        return normalize_path(os.path.dirname(self._source_path)) if self._source_path else None

    @property
    def target_dir(self) -> str | None:
        return normalize_path(os.path.dirname(self._target_path)) if self._target_path else None

    @property
    def quality(self) -> int:
        return int(self._scale_quality * 100)

    @quality.setter
    def quality(self, value: int) -> None:
        self._scale_quality = value / 100

    @property
    def position(self) -> IntVar:
        if self._positionVar is None:
            self._positionVar = IntVar(value=1)
        return self._positionVar

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
                n_frame.frame = processor.process_frame(n_frame.frame)
                result.append((n_frame.frame, processor_name))
        return result

    def get_frames(self, frame_number: int = 0, processed: bool = False) -> FramesList:
        saved_frames = self.get_previews(frame_number)
        if saved_frames:  # frame already in the cache
            return saved_frames
        frame_steps = self.get_frame_steps(frame_number, self.frame_handler, processed)
        if processed:
            self.set_previews(frame_number, frame_steps)  # cache, if processing has requested
        return frame_steps

    def update_preview(self, processed: bool | None = None) -> None:
        if processed is None:
            processed = self.is_processors_loaded
        frames = self.get_frames(self.position.get(), processed)
        if frames:
            if processed:
                self.Player.show_frame(frames[-1][0])
            else:
                self.Player.show_frame(frames[0][0])
        else:
            self.Player.clear()

    @property
    def frame_handler(self) -> BaseFrameHandler:
        if self._target_handler is None:
            if self.target_path is None:
                self._target_handler = NoneHandler('', self.parameters)
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
    def framedrop_delta(self) -> int:
        if self._framedrop_delta is None:
            self._framedrop_delta = int(self.frame_handler.fps * 5)  # 5 seconds should be enough
        return self._framedrop_delta

    @property
    def frame_step(self) -> int:
        return 1
        if self.framedrop == -1:
            return self.calculate_framedrop() + 1
        return self.framedrop + 1

    @property
    def framedrop(self) -> int:
        return self._framedrop

    @framedrop.setter
    def framedrop(self, value: int) -> None:
        self._framedrop = value

    @property
    def player_is_started(self) -> bool:
        return self._event_buffering.is_set() and self._event_playback.is_set()

    def rewind(self, frame_position: int) -> None:
        if self.player_is_started:
            self.__stop_buffering()
            self.TimeLine.rewind(frame_position - 1)
            self.__start_buffering(frame_position)
        else:
            self.update_preview()
        self.position.set(frame_position)
        self._status("Time position", seconds_to_hmsms(self.frame_handler.frame_time * (frame_position - 1)))

    def player_start(self, start_frame: int) -> None:
        if not self.player_is_started:
            self.TimeLine.reload(frame_time=self.frame_handler.frame_time, start_frame=start_frame - 1, end_frame=self.frame_handler.fc)
            self.extract_frames()
            self.__start_buffering(start_frame)
            self.__start_playback()

    def player_stop(self, wait: bool = False, reload_frames: bool = False) -> None:
        if self.player_is_started:
            self.__stop_buffering()
            self.__stop_playback()
            if self.TimeLine:
                self.TimeLine.stop()
            self._current_framedrop = 0
            if wait:
                time.sleep(1)  # Allow time for the thread to respond
            if reload_frames:
                self._is_target_frames_extracted = False

    def __start_buffering(self, start_frame: int) -> None:
        if not self._event_buffering.is_set():
            self._event_buffering.set()
            self._processed_frames_count = 0
            self._buffered_frames_count = 0
            self._process_fps = self._process_buffering(start_frame, self.frame_handler.fc)
            self.update_status(f"frames buffering is done, mean time: {self._process_fps}")

    def __stop_buffering(self) -> None:
        if self._event_buffering.is_set() and self._process_frames_thread:
            self.ProgressBarsManager.done(BUFFERING_PROGRESS_NAME)
            self._event_buffering.clear()
            self._processed_frames_count = 0
            self._process_frames_thread.join(1)
            self._process_frames_thread = None

    def _process_buffering(self, start_frame: int, end_frame: int) -> float:
        """
        Pre-process some frames and calculates mean processing frame time
        :param start_frame: frame to start with
        :param end_frame: last frame number (end of vide0)
        :returns mean processing time for a frame
        """
        def buffering_done(future_: Future[float | None]) -> None:
            process_time = future_.result()
            if process_time:
                results.append(process_time)
            futures.remove(future_)
            if self._event_buffering.is_set():  # need to check to avoid ghost progressbar
                self._buffered_frames_count += 1
                # зависает!
                # self.ProgressBarsManager.update(name=BUFFERING_PROGRESS_NAME, value=self._buffered_frames_count, max_value=self._initial_frame_buffer_length)

        futures: list[Future[None]] = []
        results: list[float] = []
        self._buffered_frames_count: int = 0

        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            while (self._buffered_frames_count < self._initial_frame_buffer_length) or (start_frame >= end_frame):
                if self.TimeLine.has_frame(start_frame):
                    start_frame += 1  # skip, if already rendered
                    continue
                self.update_status(f"submitting {start_frame}")
                future: Future[float | None] = executor.submit(self._process_frame, start_frame)
                future.add_done_callback(buffering_done)
                futures.append(future)
                start_frame += 1

                if len(futures) > self._initial_frame_buffer_length:
                    executor.shutdown()
                    break

                self._status("Memory usage(resident/virtual)", self.get_mem_usage())

                if not self._event_buffering.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    self.ProgressBarsManager.done(BUFFERING_PROGRESS_NAME)
                    break
            self.update_status("_process_buffering loop done")
            return sum(results)/len(results)

    def __start_playback(self) -> None:
        if not self._event_playback.is_set():
            self._event_playback.set()
            self._shown_frames_count = 0
            self._show_frames_thread = threading.Thread(target=self._show_frames, name="_show_frames")
            self._show_frames_thread.daemon = True
            self._show_frames_thread.start()

    def __stop_playback(self) -> None:
        if self._event_playback.is_set() and self._show_frames_thread:
            self._event_playback.clear()
            self._shown_frames_count = 0
            self._show_frames_thread.join(1)  # timeout is required to avoid problem with a wiggling navigation slider
            self._show_frames_thread = None

    def _process_frames(self, start_frame: int, end_frame: int) -> None:
        """
        renders all frames between start_frame and end_frame
        :param start_frame:
        :param end_frame:
        """
        def process_done(future_: Future[None]) -> None:
            futures.remove(future_)

        futures: list[Future[None]] = []
        self._processed_frames_count = 0
        self._shown_frames_count = 0

        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:  # this adds processing operations into a queue
            while start_frame <= end_frame:
                if self.TimeLine.has_frame(start_frame):
                    start_frame += self.frame_step
                    continue
                future: Future[None] = executor.submit(self._process_frame, start_frame)
                future.add_done_callback(process_done)
                futures.append(future)
                start_frame += self.frame_step

                if len(futures) >= self.execution_threads:
                    futures[:1][0].result()

                self._status("Memory usage(resident/virtual)", self.get_mem_usage())

                if not self._event_playback.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    self.ProgressBarsManager.done(BUFFERING_PROGRESS_NAME)
                    break
            self.update_status("_process_frames loop done")

    def _process_frame(self, frame_index: int) -> float | None:
        """
        Renders a frame with the current processors set
        :param frame_index: the frame index
        :return: the render time, or None on error
        """
        try:
            n_frame = self.frame_handler.extract_frame(frame_index)
        except EOutOfRange:
            self.update_status(f"There's no frame {frame_index}")
            return None
        n_frame.frame = scale(n_frame.frame, self._scale_quality)
        with PerfCounter() as frame_render_time:
            for _, processor in self.processors.items():
                self.update_status(f"processing {frame_index}")
                n_frame.frame = processor.process_frame(n_frame.frame)
        self.TimeLine.add_frame(n_frame)
        return frame_render_time.execution_time

    def _show_frames(self) -> None:
        if self.Player:
            while self._event_playback.is_set():
                try:
                    n_frame = self.TimeLine.get_frame()
                except EOFError:
                    self.update_status("No more frames in the timeline")
                    self._event_playback.clear()
                    break
                if n_frame is None:
                    time.sleep(self.frame_handler.frame_time / 2)
                    continue
                self.Player.show_frame(n_frame.frame)
                self._shown_frames_count += 1
                if self.TimeLine.last_returned_index is None:
                    self._status("Time position", "There's no ready frames")
                else:
                    self.position.set(self.TimeLine.last_returned_index)
                    self._status("Time position", seconds_to_hmsms(self.TimeLine.last_returned_index * self.frame_handler.frame_time))
            self.update_status("_show_frames loop done")

    # return the count of the skipped frames for the next iteration
    def calculate_framedrop(self) -> int:
        previous_framedrop = self._current_framedrop
        if (self.TimeLine.last_written_index - self.framedrop_delta) > self.TimeLine.last_requested_index:  # buffering is too fast, framedrop can be decreased
            if self._current_framedrop > 0:
                self._current_framedrop -= 1
        elif self.TimeLine.last_written_index < self.TimeLine.last_requested_index:  # buffering is too slow, need to increase framedrop
            self._current_framedrop += 1

        # self.update_status(f"current_frame_drop: {self._current_framedrop} (w/r: {self.TimeLine.last_written_index}/{self.TimeLine.last_read_index}, p/s: {self._processed_frames_count}/{self._shown_frames_count})")
        if self._current_framedrop != previous_framedrop:
            self._status("Frame drop", str(self._current_framedrop))
        return self._current_framedrop

    def init_framedrop(self) -> None:
        if self._process_fps == 0:  # by some reasons it is not inited
            self._current_framedrop = 0
        else:
            self._current_framedrop = round(self.frame_handler.fps / self._process_fps) - 1
        if self._current_framedrop < 0:
            self._current_framedrop = 0

    def extract_frames(self) -> bool:
        if self._prepare_frames is not False and not self._is_target_frames_extracted:
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
                        self.ProgressBarsManager.update(name=EXTRACTING_PROGRESS_NAME, value=state.processed_frames_count, max_value=state.frames_count)
                    self.ProgressBarsManager.done(EXTRACTING_PROGRESS_NAME)

            frame_extractor.release_resources()
            if state_is_finished:
                self._target_handler = DirectoryHandler(state.path, self.parameters, self.frame_handler.fps, self.frame_handler.fc, self.frame_handler.resolution)
            self._is_target_frames_extracted = state_is_finished
        return self._is_target_frames_extracted

    @staticmethod
    def get_mem_usage() -> str:
        mem_rss = get_mem_usage()
        mem_vms = get_mem_usage('vms')
        return '{:.2f}'.format(mem_rss).zfill(5) + '/' + '{:.2f}'.format(mem_vms).zfill(5) + ' MB'
