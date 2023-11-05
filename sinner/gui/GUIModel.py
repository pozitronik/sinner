import os
import threading
import time
from argparse import Namespace
from asyncio import Future
from concurrent.futures.thread import ThreadPoolExecutor
from enum import Enum
from tkinter import IntVar
from typing import List

from tqdm import tqdm

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.Status import Status, Mood
from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.gui.controls.SimpleStatusBar import SimpleStatusBar
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
from sinner.utilities import list_class_descendants, resolve_relative_path, suggest_execution_threads, suggest_temp_dir, iteration_mean, seconds_to_hmsms
from sinner.validators.AttributeLoader import Rules


class FrameMode(Enum):
    ALL = "Play all frames"
    SKIP = "Skip frames to match the original speed"


class GUIModel(Status):
    # configuration variables
    frame_processor: List[str]
    _source_path: str
    _target_path: str
    temp_dir: str
    execution_threads: int
    bootstrap_processors: bool  # bootstrap_processors processors on startup
    _prepare_frames: bool | None  # True: always extract and use, False: newer extract nor use, Null: newer extract, use if exists
    _initial_frame_buffer_length: int  # frames needs to be rendered before player start. Also used to determine initial frame drop
    _scale_quality: float  # the processed frame size scale from 0 to 1
    _frame_mode: FrameMode

    parameters: Namespace

    # internal/external objects
    _processors: dict[str, BaseFrameProcessor]  # cached processors for gui [processor_name, processor]
    _target_handler: BaseFrameHandler | None = None  # the initial handler of the target file
    _player: BaseFramePlayer | None = None
    _positionVar: IntVar | None = None

    _previews: dict[int, FramesList] = {}  # position: [frame, caption]  # todo: make a component or modify FrameThumbnails
    status_bar: SimpleStatusBar | None = None

    # player counters
    _processed_frames_count: int = 0  # the overall count of processed frames
    _shown_frames_count: int = 0  # the overall count of shown frames
    _current_frame_drop: int = 0  # the current value of frames skipped on each processing iteration
    _framedrop_delta: int | None = None  # the required index of preprocessed frames

    _process_fps: float = 0

    _timeline: FrameTimeLine | None = None

    # internal variables
    _is_target_frames_prepared: bool = False

    # threads
    _process_frames_thread: threading.Thread | None = None
    _show_frames_thread: threading.Thread | None = None

    # threads control events
    _event_buffering: Event
    _event_playback: Event
    _event_stop_player: Event  # the event to stop live player

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

    #  debug only
    def status(self, item: str, value: str):
        with threading.Lock():
            if self.status_bar is not None:
                self.status_bar.set_item(item, value)

    def __init__(self, parameters: Namespace):
        self._frame_mode: FrameMode = FrameMode.SKIP
        self.parameters = parameters
        super().__init__(parameters)
        self._processors = {}
        if self.bootstrap_processors:
            self._processors = self.processors

        self._event_buffering = Event(on_set_callback=lambda: self.status("BUFFERING", "ON"), on_clear_callback=lambda: self.status("BUFFERING", "OFF"))
        self._event_playback = Event(on_set_callback=lambda: self.status("PLAYBACK", "ON"), on_clear_callback=lambda: self.status("PLAYBACK", "OFF"))
        self._event_stop_player = Event(on_set_callback=lambda: self.status("STOP", "ON"), on_clear_callback=lambda: self.status("STOP", "OFF"))

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

        if self.player_is_playing:  # todo: возможно оно и не надо
            self.player_stop()
            self.player_start(start_frame=self._timeline.last_read_index, player=self.player)
        else:
            self.update_preview()

    @property
    def target_path(self) -> str | None:
        return self._target_path

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        self.parameters.target = value
        self.reload_parameters()
        self.player.clear()
        self.position.set(0)

        if self.player_is_playing:
            self.player_stop(reload_frames=True)
            self.player_start(start_frame=self._timeline.last_read_index, player=self.player)
        else:
            self.update_preview()

    @property
    def source_dir(self) -> str | None:
        return os.path.dirname(self._source_path) if self._source_path else None

    @property
    def target_dir(self) -> str | None:
        return os.path.dirname(self._target_path) if self._target_path else None

    @property
    def player(self) -> BaseFramePlayer | None:
        return self._player

    @player.setter
    def player(self, value: BaseFramePlayer | None) -> None:
        self._player = value

    @property
    def quality(self) -> int:
        return int(self._scale_quality * 100)

    @quality.setter
    def quality(self, value: int) -> None:
        self._scale_quality = value / 100

    @property
    def position(self) -> IntVar:
        if self._positionVar is None:
            self._positionVar = IntVar()
        return self._positionVar

    def rewind(self, frame_position: int) -> None:
        if self.player_is_playing:
            self.player_stop()
            self.player_start(start_frame=frame_position, player=self.player)
        else:
            self.update_preview()
        self.position.set(frame_position)

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
                self.player.show_frame(frames[-1][0])
            else:
                self.player.show_frame(frames[0][0])
        else:
            self.player.clear()

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
    def framedrop_delta(self) -> int:
        if self._framedrop_delta is None:
            self._framedrop_delta = int(self.frame_handler.fps * 5)  # 5 seconds should be enough
        return self._framedrop_delta

    @property
    def frame_step(self) -> int:
        if self._frame_mode is FrameMode.ALL:
            return 1
        if self._frame_mode is FrameMode.SKIP:
            return self.calculate_framedrop() + 1

    def player_start(self, start_frame: int, player: BaseFramePlayer) -> None:
        if player:
            self.player = player
        self._timeline = FrameTimeLine(frame_time=self.frame_handler.frame_time, start_frame=start_frame)
        if self._prepare_frames is not False and not self._is_target_frames_prepared:
            self._is_target_frames_prepared = self.extract_frames()

        self._event_stop_player.clear()
        self.__start_buffering(start_frame)  # it also will start the player thread

    def player_stop(self, wait: bool = False, reload_frames: bool = False) -> None:
        self._event_stop_player.set()
        self.__stop_playback()
        self.__stop_buffering()
        if self._timeline:
            self._timeline.stop()
        self._current_frame_drop = 0
        if wait:
            time.sleep(1)  # Allow time for the thread to respond
        if reload_frames:
            self._is_target_frames_prepared = False

    def __start_buffering(self, start_frame: int):
        if not self._event_buffering.is_set():
            self._processed_frames_count = 0
            self._process_frames_thread = threading.Thread(target=self._process_frames, name="_process_frames", kwargs={
                'start_frame': start_frame,
                'end_frame': self.frame_handler.fc
            })
            self._process_frames_thread.daemon = True
            self._process_frames_thread.start()
            self._event_buffering.set()

    def __stop_buffering(self):
        if self._event_buffering.is_set() and self._process_frames_thread:
            self._process_frames_thread.join(1)
            self._process_frames_thread = None
            self._event_buffering.clear()

    def __start_playback(self):
        if not self._event_playback.is_set():
            self._shown_frames_count = 0
            self._show_frames_thread = threading.Thread(target=self._show_frames, name="_show_frames")
            self._show_frames_thread.daemon = True
            self._show_frames_thread.start()
            self._event_playback.set()

    def __stop_playback(self):
        if self._event_playback.is_set() and self._show_frames_thread:
            self._show_frames_thread.join(1)  # timeout is required to avoid problem with a wiggling navigation slider
            self._show_frames_thread = None
            self._event_playback.clear()

    def _process_frames(self, start_frame: int, end_frame: int) -> None:
        def process_done(future_: Future[None]) -> None:
            futures.remove(future_)
            if self._processed_frames_count >= self._initial_frame_buffer_length and not self._event_playback.is_set():  # todo: need to check, it calls after every restart
                self._current_frame_drop = round(self.frame_handler.fps / self._process_fps) - 1
                if self._current_frame_drop < 0:
                    self._current_frame_drop = 0
                self.__start_playback()
            elif not self._event_playback.is_set():
                self.update_status(f"Waiting to fill the buffer: {self._processed_frames_count} of {self._initial_frame_buffer_length}")

        futures: list[Future[None]] = []
        self._processed_frames_count = 0
        self._shown_frames_count = 0
        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:  # this adds processing operations into a queue
            while start_frame < end_frame:
                future: Future[None] = executor.submit(self._process_frame, start_frame)
                future.add_done_callback(process_done)
                futures.append(future)
                start_frame += self.frame_step

                if len(futures) >= self.execution_threads:
                    futures[:1][0].result()

                if self._event_stop_player.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    def _process_frame(self, frame_index: int) -> None:
        if not self._event_stop_player.is_set():
            with PerfCounter() as frame_render_time:
                n_frame = self.frame_handler.extract_frame(frame_index)
                n_frame.frame = scale(n_frame.frame, self._scale_quality)
                for _, processor in self.processors.items():
                    n_frame.frame = processor.process_frame(n_frame.frame)
            self._timeline.add_frame(n_frame)
            self._processed_frames_count += 1
            self._process_fps = iteration_mean(1 / frame_render_time.execution_time, self._process_fps, self._processed_frames_count)

    def _show_frames(self) -> None:
        if self.player:
            while not self._event_stop_player.is_set():
                n_frame = self._timeline.get_frame()
                if n_frame is None:
                    time.sleep(self.frame_handler.frame_time / 2)
                    continue
                self.player.show_frame(n_frame.frame)
                self._shown_frames_count += 1
                self.position.set(self._timeline.last_read_index)
                self.status("time", seconds_to_hmsms(self._timeline.time_position()))

    # return the count of the skipped frames for the next iteration
    def calculate_framedrop(self) -> int:
        if (self._timeline.last_written_index - self.framedrop_delta) > self._timeline.last_read_index:  # buffering is too fast, framedrop can be decreased
            if self._current_frame_drop > 0:
                self._current_frame_drop -= 1
        elif self._timeline.last_written_index < self._timeline.last_read_index:  # buffering is too slow, need to increase framedrop
            self._current_frame_drop += 1

        # self.update_status(f"current_frame_drop: {self._current_frame_drop} (w/r: {self._timeline.last_written_index}/{self._timeline.last_read_index}, p/s: {self._processed_frames_count}/{self._shown_frames_count})")
        return self._current_frame_drop

    def extract_frames(self) -> bool:
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
