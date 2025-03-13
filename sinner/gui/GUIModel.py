import os
import threading
import time
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor, Future
from tkinter import IntVar
from typing import List, Callable, Any

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.gui.controls.FramePlayer.PygameFramePlayer import PygameFramePlayer
from sinner.gui.controls.ProgressIndicator.BaseProgressIndicator import BaseProgressIndicator
from sinner.handlers.frame.EOutOfRange import EOutOfRange
from sinner.models.FrameTimeLine import FrameTimeLine
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.NoneHandler import NoneHandler
from sinner.helpers.FrameHelper import scale
from sinner.models.Event import Event
from sinner.models.MovingAverage import MovingAverage
from sinner.models.PerfCounter import PerfCounter
from sinner.models.State import State
from sinner.models.audio.BaseAudioBackend import BaseAudioBackend
from sinner.models.status.StatusMixin import StatusMixin
from sinner.models.status.Mood import Mood
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.processors.frame.FrameExtractor import FrameExtractor
from sinner.utilities import list_class_descendants, resolve_relative_path, suggest_execution_threads, suggest_temp_dir, seconds_to_hmsms, normalize_path, get_mem_usage
from sinner.validators.AttributeLoader import Rules, AttributeLoader

BUFFERING_PROGRESS_NAME = "Buffering"
EXTRACTING_PROGRESS_NAME = "Extracting"
PROCESSING = 1
PROCESSED = 2
EXTRACTED = 3


class GUIModel(AttributeLoader, StatusMixin):
    # configuration variables
    frame_processor: List[str]
    _source_path: str
    _target_path: str
    temp_dir: str
    execution_threads: int
    bootstrap_processors: bool  # bootstrap_processors processors on startup
    _prepare_frames: bool  # True: always extract and use, False: newer extract nor use, Null: newer extract, use if exists. Note: attribute can't be typed as bool | None due to AttributeLoader limitations
    _scale_quality: float  # the processed frame size scale from 0 to 1
    _enable_sound: bool
    _audio_backend: str  # the current audio backend class name, used to create it in the factory

    parameters: Namespace

    # internal/external objects
    TimeLine: FrameTimeLine
    Player: BaseFramePlayer
    _ProgressBar: BaseProgressIndicator | None = None
    AudioPlayer: BaseAudioBackend | None = None

    _processors: dict[str, BaseFrameProcessor]  # cached processors for gui [processor_name, processor]
    _target_handler: BaseFrameHandler | None = None  # the initial handler of the target file
    _positionVar: IntVar | None = None
    _volumeVar: IntVar | None = None

    _status: Callable[[str, str], Any]

    # player counters
    _framedrop: int = -1  # the manual value of dropped frames

    _processing_fps: float = 1

    # internal variables
    _is_target_frames_extracted: bool = False
    _biggest_processed_frame: int = 0  # the last (by number) processed frame index, needed to indicate if processing gap is too big
    _average_processing_time: MovingAverage = MovingAverage(window_size=10)  # Calculator for the average processing time
    _average_frame_skip: MovingAverage = MovingAverage(window_size=10)  # Calculator for the average frame skip

    # threads
    _process_frames_thread: threading.Thread | None = None
    _show_frames_thread: threading.Thread | None = None

    # threads control events
    _event_processing: Event  # the flag to control start/stop processing thread
    _event_playback: Event  # the flag to control start/stop processed frames playback thread
    _event_rewind: Event  # the flag to control if playback was rewound

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
                'default': 1,
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
                'parameter': ['sound', 'enable-sound'],
                'attribute': '_enable_sound',
                'default': True,
                'help': 'Enable audio playback'
            },
            {
                'parameter': ['audio-backend', 'audio'],
                'attribute': '_audio_backend',
                'default': 'VLCAudioBackend',
                'choices': list_class_descendants(resolve_relative_path('../models/audio'), 'BaseAudioBackend'),
                'help': 'Audio backend to use'
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

    def __init__(self, parameters: Namespace, status_callback: Callable[[str, str], Any], on_close_event: Event | None = None, progress_control: BaseProgressIndicator | None = None):
        self.parameters = parameters
        super().__init__(parameters)
        self._processors = {}
        if self.bootstrap_processors:
            self._processors = self.processors

        self.TimeLine = FrameTimeLine(source_name=self._source_path, target_name=self._target_path, temp_dir=self.temp_dir, end_frame=self.frame_handler.fc)
        self.Player = PygameFramePlayer(width=self.frame_handler.resolution[0], height=self.frame_handler.resolution[1], caption='sinner player', on_close_event=on_close_event)

        if self._enable_sound:
            self.AudioPlayer = BaseAudioBackend.create(self._audio_backend, parameters=self.parameters, media_path=self._target_path)

        self.progress_control = progress_control
        self._status = status_callback
        self._status("Time position", seconds_to_hmsms(0))

        self._event_processing = Event()
        self._event_playback = Event()
        self._event_rewind = Event()

    def reload_parameters(self) -> None:
        self._target_handler = None
        super().__init__(self.parameters)
        for _, processor in self.processors.items():
            processor.load(self.parameters)

    def enable_sound(self, enable: bool | None = None) -> bool:
        if enable is not None:
            self._enable_sound = enable
            if self._enable_sound and not self.AudioPlayer:
                self.AudioPlayer = BaseAudioBackend.create(self._audio_backend, parameters=self.parameters, media_path=self._target_path)
            elif self.AudioPlayer:
                self.AudioPlayer.stop()
                self.AudioPlayer = None
        return self._enable_sound

    @property
    def audio_backend(self) -> str:
        return self._audio_backend

    @audio_backend.setter
    def audio_backend(self, backend: str) -> None:
        self.enable_sound(False)
        self._audio_backend = backend
        self.enable_sound(True)

    @property
    def source_path(self) -> str | None:
        return self._source_path

    @source_path.setter
    def source_path(self, value: str | None) -> None:
        self.parameters.source = value
        self.reload_parameters()
        self.TimeLine = FrameTimeLine(source_name=self._source_path, target_name=self._target_path, temp_dir=self.temp_dir, frame_time=self.frame_handler.frame_time, start_frame=self.TimeLine.last_requested_index, end_frame=self.frame_handler.fc)
        self.progress_control = self._ProgressBar  # to update segments
        if not self.player_is_started:
            self.update_preview()

    @property
    def target_path(self) -> str | None:
        return self._target_path

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        self.parameters.target = value
        self.reload_parameters()
        self.Player.clear()
        self.TimeLine = FrameTimeLine(source_name=self._source_path, target_name=self._target_path, temp_dir=self.temp_dir, frame_time=self.frame_handler.frame_time, start_frame=1, end_frame=self.frame_handler.fc)
        self.progress_control = self._ProgressBar  # to update segments
        if self._enable_sound:
            if self.AudioPlayer:
                self.AudioPlayer.stop()
            self.AudioPlayer = BaseAudioBackend.create(self._audio_backend, parameters=self.parameters, media_path=self._target_path)
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
    def volume(self) -> IntVar:
        if self._volumeVar is None:
            self._volumeVar = IntVar(value=self.AudioPlayer.volume if self.AudioPlayer else 0)
        return self._volumeVar

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

    def update_preview(self, processed: bool | None = None) -> None:
        if processed is None:
            processed = self.is_processors_loaded
        frame_number = self.position.get()
        if not processed:  # base frame requested
            try:
                preview_frame = self.frame_handler.extract_frame(frame_number)
            except Exception as exception:
                self.update_status(message=str(exception), mood=Mood.BAD)
                preview_frame = None
        else:
            if not self.TimeLine.has_index(frame_number):
                self._process_frame(frame_number)

            preview_frame = self.TimeLine.get_frame_by_index(frame_number)

        if preview_frame:
            self.Player.show_frame(preview_frame.frame)
            self.set_progress_index_value(self.position.get(), PROCESSED if processed else EXTRACTED)
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

    @property
    def player_is_started(self) -> bool:
        return self._event_processing.is_set() or self._event_playback.is_set()

    def set_volume(self, volume: int) -> None:
        if self.AudioPlayer:
            self.AudioPlayer.volume = volume

    def rewind(self, frame_position: int) -> None:
        if self.player_is_started:
            self.TimeLine.rewind(frame_position - 1)
            self._event_rewind.set(tag=frame_position - 1)
        else:
            self.update_preview()
        self.position.set(frame_position)
        if self.AudioPlayer:
            self.AudioPlayer.position = int(frame_position * self.frame_handler.frame_time)
        self._status("Time position", seconds_to_hmsms(self.frame_handler.frame_time * (frame_position - 1)))
        self._status("Frame position", f'{self.position.get()}/{self.frame_handler.fc}')

    def player_start(self, start_frame: int) -> None:
        if not self.player_is_started:
            self.TimeLine.reload(frame_time=self.frame_handler.frame_time, start_frame=start_frame - 1, end_frame=self.frame_handler.fc)
            if self.AudioPlayer:
                self.AudioPlayer.position = int(start_frame * self.frame_handler.frame_time)
            self.extract_frames()
            self.__start_processing(start_frame)  # run the main rendering process
            self.__start_playback()  # run the separate playback
            if self.AudioPlayer:
                self.AudioPlayer.play()

    def player_stop(self, wait: bool = False, reload_frames: bool = False) -> None:
        if self.player_is_started:
            if self.AudioPlayer:
                self.AudioPlayer.stop()
            self.__stop_processing()
            self.__stop_playback()
            if self.TimeLine:
                self.TimeLine.stop()
            if wait:
                time.sleep(1)  # Allow time for the thread to respond
            if reload_frames:
                self._is_target_frames_extracted = False

    def __start_processing(self, start_frame: int) -> None:
        """
        Runs the main processing thread
        :param start_frame:
        """
        if not self._event_processing.is_set():
            self._event_processing.set()
            self._process_frames_thread = threading.Thread(target=self._process_frames, name="_process_frames", kwargs={
                'next_frame': start_frame,
                'end_frame': self.frame_handler.fc
            })
            self._process_frames_thread.daemon = True
            self._process_frames_thread.start()

    def __stop_processing(self) -> None:
        if self._event_processing.is_set() and self._process_frames_thread:
            self._event_processing.clear()
            self._process_frames_thread.join(1)
            self._process_frames_thread = None

    def __start_playback(self) -> None:
        if not self._event_playback.is_set():
            self._event_playback.set()
            self._show_frames_thread = threading.Thread(target=self._show_frames, name="_show_frames")
            self._show_frames_thread.daemon = True
            self._show_frames_thread.start()

    def __stop_playback(self) -> None:
        if self._event_playback.is_set() and self._show_frames_thread:
            self._event_playback.clear()
            self._show_frames_thread.join(1)  # timeout is required to avoid problem with a wiggling navigation slider
            self._show_frames_thread = None

    def _process_frames(self, next_frame: int, end_frame: int) -> None:
        """
        renders all frames between start_frame and end_frame
        :param next_frame:
        :param end_frame:
        """

        def process_done(future_: Future[tuple[float, int] | None]) -> None:
            if not future_.cancelled():
                result = future_.result()
                if result:
                    process_time, frame_index = result
                    self._average_processing_time.update(process_time / self.execution_threads)
                    processing.remove(frame_index)
                    self.set_progress_index_value(frame_index, PROCESSED)
                    self._processing_fps = 1 / self._average_processing_time.get_average()
                    if self._biggest_processed_frame < frame_index:
                        self._biggest_processed_frame = frame_index
                    self._status("Average processing speed", f"{round(self._processing_fps, 4)} FPS")  # fixme: execution-threads=1 prevents value to display
            futures.remove(future_)

        processing: List[int] = []  # list of frames currently being processed
        futures: list[Future[tuple[float, int] | None]] = []
        processing_delta: int = 0  # additional lookahead to adjust frames synchronization

        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:  # this adds processing operations into a queue
            while next_frame <= end_frame:
                if self._event_rewind.is_set():
                    next_frame = self._event_rewind.tag or 0
                    self._event_rewind.clear()

                if next_frame not in processing and not self.TimeLine.has_index(next_frame):
                    processing.append(next_frame)
                    future: Future[tuple[float, int] | None] = executor.submit(self._process_frame, next_frame)
                    future.add_done_callback(process_done)
                    futures.append(future)
                    self.set_progress_index_value(next_frame, PROCESSING)
                    if len(futures) >= self.execution_threads:
                        futures[:1][0].result()

                    self._status("Memory usage (resident/virtual)", self.get_mem_usage())

                if not self._event_processing.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                self._average_frame_skip.update(self.frame_handler.fps / self._processing_fps)

                if self.TimeLine.last_added_index > self.TimeLine.last_requested_index + self.TimeLine.current_frame_miss and processing_delta > self._average_frame_skip.get_average():
                    processing_delta -= 1
                elif self.TimeLine.last_added_index < self.TimeLine.last_requested_index:
                    processing_delta += 1
                step = int(self._average_frame_skip.get_average()) + processing_delta
                if step < 1:  # preventing going backwards
                    step = 1
                next_frame += step
                # self.status.debug(msg=f"NEXT: {next_frame}, STEP: {step}, DELTA: {processing_delta}, LAST: {self.TimeLine.last_added_index}, AVG: {self._average_frame_skip.get_average()} ")

    def _process_frame(self, frame_index: int) -> tuple[float, int] | None:
        """
        Renders a frame with the current processors set
        :param frame_index: the frame index
        :return: the [render time, frame index], or None on error
        """
        try:
            n_frame = self.frame_handler.extract_frame(frame_index)
        except EOutOfRange:
            self.update_status(f"There's no frame {frame_index}")
            return None
        n_frame.frame = scale(n_frame.frame, self._scale_quality)
        with PerfCounter() as frame_render_time:
            for _, processor in self.processors.items():
                n_frame.frame = processor.process_frame(n_frame.frame)
                # self.status.debug(msg=f"DONE: {n_frame.index}")
        self.TimeLine.add_frame(n_frame)
        return frame_render_time.execution_time, n_frame.index

    def _show_frames(self) -> None:
        last_shown_frame_index: int = -1
        if self.Player:
            while self._event_playback.is_set():
                start_time = time.perf_counter()
                try:
                    n_frame = self.TimeLine.get_frame()
                except EOFError:
                    self._event_playback.clear()
                    break
                if n_frame is not None:
                    if n_frame.index != last_shown_frame_index:  # check if frame is really changed
                        # self.status.debug(msg=f"REQ: {self.TimeLine.last_requested_index}, SHOW: {n_frame.index}, ASYNC: {self.TimeLine.last_requested_index - n_frame.index}")
                        self.Player.show_frame(n_frame.frame)
                        last_shown_frame_index = n_frame.index
                        if self.TimeLine.last_returned_index is None:
                            self._status("Time position", "There are no ready frames")
                        else:
                            if not self._event_rewind.is_set():
                                self.position.set(self.TimeLine.last_returned_index)
                            if self.TimeLine.last_returned_index:
                                self._status("Time position", seconds_to_hmsms(self.TimeLine.last_returned_index * self.frame_handler.frame_time))
                                self._status("Frame position", f'{self.position.get()}/{self.frame_handler.fc}')
                loop_time = time.perf_counter() - start_time  # time for the current loop, sec
                sleep_time = self.frame_handler.frame_time - loop_time  # time to wait for the next loop, sec
                if sleep_time > 0:
                    time.sleep(sleep_time)

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
                frame_extractor.process(self.frame_handler, state)  # todo: return the GUI progressbar
                frame_extractor.release_resources()
            if state_is_finished:
                self._target_handler = DirectoryHandler(state.path, self.parameters, self.frame_handler.fps, self.frame_handler.fc, self.frame_handler.resolution)
            self._is_target_frames_extracted = state_is_finished
            if self._ProgressBar:
                self._ProgressBar.set_segment_values(state.processed_frames_indices, PROCESSING, False, False)
        return self._is_target_frames_extracted

    @staticmethod
    def get_mem_usage() -> str:
        mem_rss = get_mem_usage()
        mem_vms = get_mem_usage('vms')
        return '{:.2f}'.format(mem_rss).zfill(5) + '/' + '{:.2f}'.format(mem_vms).zfill(5) + ' MB'

    def set_progress_index_value(self, index: int, value: int) -> None:
        if self._ProgressBar:
            self._ProgressBar.set_segment_value(index, value)

    @property
    def progress_control(self) -> BaseProgressIndicator | None:
        return self._ProgressBar

    @progress_control.setter
    def progress_control(self, value: BaseProgressIndicator | None) -> None:
        self._ProgressBar = value
        if self._ProgressBar:
            self._ProgressBar.set_segments(self.frame_handler.fc + 1)  # todo: разобраться, почему прогрессбар требует этот один лишний индекс
            self._ProgressBar.set_segment_values(self.TimeLine.processed_frames, PROCESSED)
