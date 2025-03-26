import threading
from abc import ABC, abstractmethod
from argparse import Namespace
from tkinter import IntVar
from typing import Optional, Any, Callable

from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.gui.controls.ProgressIndicator.BaseProgressIndicator import BaseProgressIndicator
from sinner.models.Event import Event
from sinner.models.FrameTimeLine import FrameTimeLine
from sinner.models.MediaMetaData import MediaMetaData
from sinner.models.audio.BaseAudioBackend import BaseAudioBackend

BUFFERING_PROGRESS_NAME = "Buffering"
EXTRACTING_PROGRESS_NAME = "Extracting"
PROCESSING = 1
PROCESSED = 2
EXTRACTED = 3


class ProcessingModelInterface(ABC):
    """
    Interface for frame processing models.
    Defines the common API for local and remote processing implementations.
    """
    parameters: Namespace

    _source_path: Optional[str]
    _target_path: Optional[str]
    temp_dir: str
    _scale_quality: float  # the processed frame size scale from 0 to 1
    _enable_sound: bool
    _audio_backend: str  # the current audio backend class name, used to create it in the factory

    # internal/external objects
    MetaData: Optional[MediaMetaData] = None  # dataclass to store target mediainfo
    TimeLine: FrameTimeLine
    Player: BaseFramePlayer
    ProgressBar: Optional[BaseProgressIndicator] = None
    AudioPlayer: Optional[BaseAudioBackend] = None

    _status: Callable[[str, str], Any]  # status callback

    _positionVar: Optional[IntVar] = None
    _volumeVar: Optional[IntVar] = None

    # Playback thread & control event
    _event_playback: Event  # Flag to control playback thread
    _show_frames_thread: Optional[threading.Thread] = None

    def __init__(self, parameters: Namespace, status_callback: Callable[[str, str], Any],
                 on_close_event: Optional[Event] = None,
                 progress_control: Optional[BaseProgressIndicator] = None):
        """Initialize the processing model."""
        pass

    @abstractmethod
    def reload_parameters(self) -> None:
        """Reload configuration parameters and update components."""
        pass

    @abstractmethod
    def enable_sound(self, enable: Optional[bool] = None) -> bool:
        """
        Enable or disable sound playback.

        Parameters:
        enable: If provided, enables or disables sound

        Returns:
        Current sound enabled state
        """
        pass

    @abstractmethod
    def update_preview(self, processed: Optional[bool] = None) -> None:
        """
        Update the preview image.

        Parameters:
        processed: If True, shows processed frame, otherwise shows original frame
        """
        pass

    @abstractmethod
    def set_volume(self, volume: int) -> None:
        """Set audio playback volume."""
        pass

    @abstractmethod
    def rewind(self, frame_position: int) -> None:
        """
        Change playback position to specified frame.

        Parameters:
        frame_position: Target frame number
        """
        pass

    @abstractmethod
    def player_start(self, start_frame: int) -> None:
        """
        Start playback from specified frame.

        Parameters:
        start_frame: Frame to start playback from
        """
        pass

    @abstractmethod
    def player_stop(self, wait: bool = False, reload_frames: bool = False, shutdown: bool = False) -> None:
        """
        Stop playback.

        Parameters:
        wait: If True, wait for threads to stop
        reload_frames: If True, reload frames on next start
        shutdown: useful for remote connections, shutdown everything
        """
        pass

    def set_progress_index_value(self, index: int, value: int) -> None:
        """Update the progress indicator for a frame."""
        if self.ProgressBar:
            self.ProgressBar.set_segment_value(index, value)

    # Properties
    @property
    @abstractmethod
    def audio_backend(self) -> str:
        """Get the current audio backend name."""
        pass

    @audio_backend.setter
    @abstractmethod
    def audio_backend(self, backend: str) -> None:
        """Set the audio backend."""
        pass

    @property
    @abstractmethod
    def source_path(self) -> Optional[str]:
        """Get the current source path."""
        pass

    @source_path.setter
    @abstractmethod
    def source_path(self, value: Optional[str]) -> None:
        """Set the source path and update related components."""
        pass

    @property
    @abstractmethod
    def target_path(self) -> Optional[str]:
        """Get the current target path."""
        pass

    @target_path.setter
    @abstractmethod
    def target_path(self, value: Optional[str]) -> None:
        """Set the target path and update related components."""
        pass

    @property
    @abstractmethod
    def source_dir(self) -> Optional[str]:
        """Get the directory containing the source file."""
        pass

    @property
    @abstractmethod
    def target_dir(self) -> Optional[str]:
        """Get the directory containing the target file."""
        pass

    @property
    @abstractmethod
    def quality(self) -> int:
        """Get the processing quality as a percentage (0-100)."""
        pass

    @quality.setter
    @abstractmethod
    def quality(self, value: int) -> None:
        """Set the processing quality from a percentage."""
        pass

    @property
    @abstractmethod
    def position(self) -> IntVar:
        """Get the current position variable for GUI controls."""
        pass

    @property
    @abstractmethod
    def volume(self) -> IntVar:
        """Get the current volume variable for GUI controls."""
        pass

    @property
    @abstractmethod
    def player_is_started(self) -> bool:
        """Check if playback is active."""
        pass

    @property
    @abstractmethod
    def metadata(self) -> MediaMetaData:
        """Processed target mediadata"""
        pass

    @property
    def progress_control(self) -> Optional[BaseProgressIndicator]:
        """Get the current progress indicator control."""
        return self.ProgressBar

    @progress_control.setter
    def progress_control(self, value: Optional[BaseProgressIndicator]) -> None:
        """Set the progress indicator control."""
        self.ProgressBar = value
        if self.ProgressBar:
            self.ProgressBar.set_segments(self.metadata.frames_count + 1)  # todo: разобраться, почему прогрессбар требует этот один лишний индекс
            self.ProgressBar.set_segment_values(self.TimeLine.processed_frames, PROCESSED)
