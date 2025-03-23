from abc import ABC, abstractmethod
from argparse import Namespace
from tkinter import IntVar
from typing import Optional, Any, Callable

from sinner.gui.controls.ProgressIndicator.BaseProgressIndicator import BaseProgressIndicator
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.models.Event import Event


class ProcessingModelInterface(ABC):
    """
    Interface for frame processing models.
    Defines the common API for local and remote processing implementations.
    """

    @abstractmethod
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
    def update_preview(self, processed: bool = True) -> None:
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
    def player_stop(self, wait: bool = False, reload_frames: bool = False) -> None:
        """
        Stop playback.

        Parameters:
        wait: If True, wait for threads to stop
        reload_frames: If True, reload frames on next start
        """
        pass

    @abstractmethod
    def set_progress_index_value(self, index: int, value: int) -> None:
        """Update the progress indicator for a frame."""
        pass

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
    def frame_handler(self) -> BaseFrameHandler:
        """Get the frame handler for the current target."""
        pass

    @property
    @abstractmethod
    def player_is_started(self) -> bool:
        """Check if playback is active."""
        pass

    @property
    @abstractmethod
    def progress_control(self) -> Optional[BaseProgressIndicator]:
        """Get the current progress indicator control."""
        pass

    @progress_control.setter
    @abstractmethod
    def progress_control(self, value: Optional[BaseProgressIndicator]) -> None:
        """Set the progress indicator control."""
        pass
