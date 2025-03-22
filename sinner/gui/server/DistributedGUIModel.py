import os
import threading
import time
from argparse import Namespace
from tkinter import IntVar
from typing import List, Callable, Any, Optional

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.gui.controls.FramePlayer.PygameFramePlayer import PygameFramePlayer
from sinner.gui.controls.ProgressIndicator.BaseProgressIndicator import BaseProgressIndicator
from sinner.gui.server.DistributedProcessingSystem import DistributedProcessingSystem
from sinner.gui.server.FrameProcessorClient import FrameProcessorClient
from sinner.gui.server.api.ZMQClientAPI import ZMQClientAPI
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.NoneHandler import NoneHandler
from sinner.models.Event import Event
from sinner.models.FrameTimeLine import FrameTimeLine
from sinner.models.MovingAverage import MovingAverage
from sinner.models.audio.BaseAudioBackend import BaseAudioBackend
from sinner.models.status.StatusMixin import StatusMixin
from sinner.models.status.Mood import Mood
from sinner.utilities import normalize_path, seconds_to_hmsms, list_class_descendants, resolve_relative_path, suggest_execution_threads, suggest_temp_dir
from sinner.validators.AttributeLoader import Rules, AttributeLoader

PROCESSING = 1
PROCESSED = 2
EXTRACTED = 3


class DistributedGUIModel(AttributeLoader, StatusMixin):
    """
    GUI model that uses distributed processing.
    This is a complete implementation without inheriting from GUIModel.
    """

    # Configuration parameters
    frame_processor: List[str]
    _source_path: str
    _target_path: str
    temp_dir: str
    execution_threads: int
    bootstrap_processors: bool
    _prepare_frames: bool  # True: always extract and use, False: never extract nor use, None: never extract, use if exists
    _scale_quality: float  # Process frame size scale from 0 to 1
    _enable_sound: bool
    _audio_backend: str  # Current audio backend class name
    endpoint: str

    # Components
    parameters: Namespace
    TimeLine: FrameTimeLine
    Player: BaseFramePlayer
    _ProgressBar: Optional[BaseProgressIndicator] = None
    AudioPlayer: Optional[BaseAudioBackend] = None
    _processor_client: Optional[FrameProcessorClient] = None  # Client side

    # Internal state
    _distributed_system: Optional[DistributedProcessingSystem] = None
    _target_handler: Optional[BaseFrameHandler] = None  # Initial handler for the target file
    _positionVar: Optional[IntVar] = None
    _volumeVar: Optional[IntVar] = None

    # Internal processing state
    _event_playback: Event  # Flag to control playback thread
    _event_synchronizing: Event  # Flag to control synchronizing threa
    _synchronize_frames_thread: Optional[threading.Thread] = None
    _show_frames_thread: Optional[threading.Thread] = None

    # Processing metrics
    _average_frame_skip: MovingAverage = MovingAverage(window_size=10)  # Average frame skip calculator
    _processing_fps: float = 1.0  # Processing speed in FPS

    # Status callback
    _status: Callable[[str, str], Any]

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'frame-processor', 'processor', 'processors'},
                'attribute': 'frame_processor',
                'default': ['FaceSwapper'],
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('../../processors/frame'), 'BaseFrameProcessor'),
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
                'choices': list_class_descendants(resolve_relative_path('../../models/audio'), 'BaseAudioBackend'),
                'help': 'Audio backend to use'
            },
            {
                'parameter': 'temp-dir',
                'default': lambda: suggest_temp_dir(self.temp_dir),
                'help': 'Select the directory for temporary files'
            },
            {
                'parameter': 'endpoint',
                'attribute': 'endpoint',
                'default': "tcp://127.0.0.1:5555",
                'help': 'Endpoint for the frame processor server'
            },
            {
                'module_help': 'Distributed GUI processing model'
            }
        ]

    def __init__(self, parameters: Namespace, status_callback: Callable[[str, str], Any], on_close_event: Optional[Event] = None, progress_control: Optional[BaseProgressIndicator] = None):
        """
        Initialize the distributed GUI model.

        Parameters:
        parameters (Namespace): Application parameters
        status_callback (Callable): Function to call with status updates
        on_close_event (Event, optional): Event to trigger on window close
        progress_control (BaseProgressIndicator, optional): Progress indicator control
        """
        self.parameters = parameters
        super().__init__(parameters)

        # Initialize distributed processing system
        self._distributed_system = DistributedProcessingSystem(self.parameters)

        # Set up the timeline and player
        self.TimeLine = FrameTimeLine(source_name=self._source_path, target_name=self._target_path, temp_dir=self.temp_dir, end_frame=self.frame_handler.fc)
        self.Player = PygameFramePlayer(width=self.frame_handler.resolution[0], height=self.frame_handler.resolution[1], caption='sinner distributed player', on_close_event=on_close_event)

        # Initialize audio if enabled
        if self._enable_sound:
            self.AudioPlayer = BaseAudioBackend.create(self._audio_backend, parameters=self.parameters, media_path=self._target_path)

        # Initialize processor client
        self._processor_client = FrameProcessorClient(ZMQClientAPI(reply_endpoint=self.endpoint))
        if self._source_path and self._target_path:
            self._processor_client.source_path = self._source_path
        if self._target_path:
            self._processor_client.target_path = self._target_path

        # Set progress control and status callback
        self.progress_control = progress_control
        self._status = status_callback
        self._status("Time position", seconds_to_hmsms(0))

        # Initialize event flags
        self._event_playback = Event()
        self._event_synchronizing = Event()

        self.update_status("Distributed GUI model initialized")

    def reload_parameters(self) -> None:
        """Reload parameters and update components."""
        self._target_handler = None
        AttributeLoader().__init__(self.parameters)

    def enable_sound(self, enable: bool | None = None) -> bool:
        """
        Enable or disable sound playback.

        Parameters:
        enable (bool, optional): If provided, enables or disables sound

        Returns:
        bool: Current sound enabled state
        """
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
        """Get the current audio backend name."""
        return self._audio_backend

    @audio_backend.setter
    def audio_backend(self, backend: str) -> None:
        """Set the audio backend."""
        self.enable_sound(False)
        self._audio_backend = backend
        self.enable_sound(True)

    @property
    def source_path(self) -> str | None:
        """Get the current source path."""
        return self._source_path

    @source_path.setter
    def source_path(self, value: str | None) -> None:
        """Set the source path and update related components."""
        self.parameters.source = value
        self.reload_parameters()

        # Update timeline
        self.TimeLine = FrameTimeLine(source_name=self._source_path, target_name=self._target_path, temp_dir=self.temp_dir, frame_time=self.frame_handler.frame_time, start_frame=self.TimeLine.last_requested_index, end_frame=self.frame_handler.fc)

        # Update progress control
        self.progress_control = self._ProgressBar

        # Update source in processor client
        self._processor_client.source_path = self.source_path

        # Update preview if not playing
        if not self.player_is_started:
            self.update_preview()

    @property
    def target_path(self) -> str | None:
        """Get the current target path."""
        return self._target_path

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        """Set the target path and update related components."""
        self.parameters.target = value
        self.reload_parameters()

        # Clear player and reset timeline
        self.Player.clear()
        self.TimeLine = FrameTimeLine(source_name=self._source_path, target_name=self._target_path, temp_dir=self.temp_dir, frame_time=self.frame_handler.frame_time, start_frame=1, end_frame=self.frame_handler.fc)
        # Update progress control
        self.progress_control = self._ProgressBar

        # Update audio if enabled
        if self._enable_sound:
            if self.AudioPlayer:
                self.AudioPlayer.stop()
            self.AudioPlayer = BaseAudioBackend.create(self._audio_backend, parameters=self.parameters, media_path=self._target_path)
        # Update target in processor client
        self._processor_client.target_path = self.target_path

        # Update playback state
        if self.player_is_started:
            self.player_stop(reload_frames=True)
            self.position.set(1)
            self.player_start(start_frame=1)
        else:
            self.update_preview()

    @property
    def source_dir(self) -> str | None:
        """Get the directory containing the source file."""
        return normalize_path(os.path.dirname(self._source_path)) if self._source_path else None

    @property
    def target_dir(self) -> str | None:
        """Get the directory containing the target file."""
        return normalize_path(os.path.dirname(self._target_path)) if self._target_path else None

    @property
    def quality(self) -> int:
        """Get the processing quality as a percentage (0-100)."""
        return int(self._scale_quality * 100)

    @quality.setter
    def quality(self, value: int) -> None:
        """Set the processing quality from a percentage."""
        self._scale_quality = value / 100

    @property
    def position(self) -> IntVar:
        """Get the current position variable for GUI controls."""
        if self._positionVar is None:
            self._positionVar = IntVar(value=1)
        return self._positionVar

    @property
    def volume(self) -> IntVar:
        """Get the current volume variable for GUI controls."""
        if self._volumeVar is None:
            self._volumeVar = IntVar(value=self.AudioPlayer.volume if self.AudioPlayer else 0)
        return self._volumeVar

    @property
    def frame_handler(self) -> BaseFrameHandler:
        """Get the frame handler for the current target."""
        if self._target_handler is None:
            if self.target_path is None:
                self._target_handler = NoneHandler('', self.parameters)
            else:
                self._target_handler = BatchProcessingCore.suggest_handler(self.target_path, self.parameters)
        return self._target_handler

    @property
    def player_is_started(self) -> bool:
        """Check if playback is active."""
        return self._event_playback.is_set()

    def update_preview(self, processed: bool = True) -> None:
        """
        Update the preview image.

        Parameters:
        processed (bool): If True, shows processed frame, otherwise shows original frame
        """
        frame_number = self.position.get()

        if not processed:  # base frame requested
            try:
                preview_frame = self.frame_handler.extract_frame(frame_number)
            except Exception as exception:
                self.update_status(message=str(exception), mood=Mood.BAD)
                preview_frame = None
        else:
            # Check if frame is already in timeline
            if not self.TimeLine.has_index(frame_number):
                # If not, check if it's processed on the server
                # todo: request frame processing on server immediately
                self._processor_client.await_frame(frame_number)
                # Try to get the frame from timeline
            preview_frame = self.TimeLine.get_frame_by_index(frame_number)

        # Display frame if available
        if preview_frame:
            self.Player.show_frame(preview_frame.frame)
            self.set_progress_index_value(self.position.get(), PROCESSED if processed else EXTRACTED)
        else:
            self.Player.clear()

    def set_volume(self, volume: int) -> None:
        """Set audio playback volume."""
        if self.AudioPlayer:
            self.AudioPlayer.volume = volume

    def rewind(self, frame_position: int) -> None:
        """
        Change playback position to specified frame.

        Parameters:
        frame_position (int): Target frame number
        """
        if self.player_is_started:
            self.TimeLine.rewind(frame_position - 1)
        else:
            self.update_preview()

        self.position.set(frame_position)

        if self.AudioPlayer:
            self.AudioPlayer.position = int(frame_position * self.frame_handler.frame_time)

        self._status("Time position", seconds_to_hmsms(self.frame_handler.frame_time * (frame_position - 1)))
        self._status("Frame position", f'{self.position.get()}/{self.frame_handler.fc}')

        # Update server with new requested position
        if self._processor_client:
            self._processor_client.rewind(frame_position)

    def player_start(self, start_frame: int) -> None:
        """
        Start playback from specified frame.

        Parameters:
        start_frame (int): Frame to start playback from
        """
        if not self.player_is_started:
            self.TimeLine.reload(frame_time=self.frame_handler.frame_time, start_frame=start_frame - 1, end_frame=self.frame_handler.fc)
            if self.AudioPlayer:
                self.AudioPlayer.position = int(start_frame * self.frame_handler.frame_time)

            # Start processing and playback threads
            self.__start_processing(start_frame)
            self.__start_playback()

            if self.AudioPlayer:
                self.AudioPlayer.play()

    def player_stop(self, wait: bool = False, reload_frames: bool = False, shutdown: bool = False) -> None:
        """
        Stop playback.

        Parameters:
        wait (bool): If True, wait for threads to stop
        reload_frames (bool): If True, reload frames on next start
        """
        if self.player_is_started:
            if self.AudioPlayer:
                self.AudioPlayer.stop()

            self.__stop_processing()
            self.__stop_playback()

            if self.TimeLine:
                self.TimeLine.stop()

            # Shutdown distributed system if enabled
            if shutdown and self._distributed_system:
                self._distributed_system.shutdown()

            if wait:
                time.sleep(1)  # Allow time for threads to stop

    def __start_processing(self, start_frame: int) -> None:
        """
        Start the processing thread.

        Parameters:
        start_frame (int): Frame to start processing from
        """

        self._processor_client.start(start_frame)

    def __stop_processing(self) -> None:
        """Stop the processing thread."""
        if self._event_synchronizing.is_set() and self._synchronize_frames_thread:
            self._event_synchronizing.clear()
            self._synchronize_frames_thread.join(1)
            self._synchronize_frames_thread = None

    def __start_playback(self) -> None:
        """Start the playback thread."""
        if not self._event_playback.is_set():
            self._event_playback.set()

            self._show_frames_thread = threading.Thread(target=self._show_frames, name="_show_frames")
            self._show_frames_thread.daemon = True
            self._show_frames_thread.start()

    def __stop_playback(self) -> None:
        """Stop the playback thread."""
        if self._event_playback.is_set() and self._show_frames_thread:
            self._event_playback.clear()
            self._show_frames_thread.join(1)
            self._show_frames_thread = None

    def _show_frames(self) -> None:
        """Thread that displays frames for playback."""
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
                    if n_frame.index != last_shown_frame_index:  # Check if frame really changed
                        self.Player.show_frame(n_frame.frame)
                        last_shown_frame_index = n_frame.index

                        if self.TimeLine.last_returned_index is None:
                            self._status("Time position", "There are no ready frames")
                        else:
                            self.position.set(self.TimeLine.last_returned_index)

                            if self.TimeLine.last_returned_index:
                                self._status("Time position", seconds_to_hmsms(self.TimeLine.last_returned_index * self.frame_handler.frame_time))
                                self._status("Frame position", f'{self.position.get()}/{self.frame_handler.fc}')

                loop_time = time.perf_counter() - start_time  # Time for the current loop
                sleep_time = self.frame_handler.frame_time - loop_time  # Time to wait for next loop

                if sleep_time > 0:
                    time.sleep(sleep_time)

    def set_progress_index_value(self, index: int, value: int) -> None:
        """Update the progress indicator for a frame."""
        if self._ProgressBar:
            self._ProgressBar.set_segment_value(index, value)

    @property
    def progress_control(self) -> Optional[BaseProgressIndicator]:
        """Get the current progress indicator control."""
        return self._ProgressBar

    @progress_control.setter
    def progress_control(self, value: Optional[BaseProgressIndicator]) -> None:
        """Set the progress indicator control."""
        self._ProgressBar = value
        if self._ProgressBar:
            self._ProgressBar.set_segments(self.frame_handler.fc + 1)
            self._ProgressBar.set_segment_values(self.TimeLine.processed_frames, PROCESSED)
