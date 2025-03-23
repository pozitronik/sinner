from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class MediaMetaData:
    """
    Data class for storing video metadata and parameters.
    """
    resolution: Tuple[int, int] = (0, 0)  # (width, height)
    fps: float = 0  # Frames per second
    frames_count: int = 0  # Total number of frames

    @property
    def length(self) -> Optional[float]:
        """
        Calculate video length in seconds.

        Returns:
            float: Video duration in seconds
        """
        return self.frames_count / self.fps if self.fps > 0 else None

    @property
    def frame_time(self) -> float:
        """
        Calculate frame time in seconds.

        Returns:
            float: Frame time in seconds
        """
        return 1 / self.fps if self.fps > 0 else 0.0

    def get_formatted_length(self) -> str:
        """
        Get formatted video length as HH:MM:SS.

        Returns:
            str: Formatted video duration
        """
        total_seconds = int(self.length)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_formatted_resolution(self) -> str:
        """
        Get formatted resolution string.
        Returns:
            str: Resolution in format "WIDTHxHEIGHT"
        """
        return f"{self.resolution[0]}x{self.resolution[1]}"

    def __str__(self) -> str:
        """
        Get all formatted data
        Returns:
            str: Resolution in format "WIDTHxHEIGHT@FPS"
        """
        """Format target resolution and framerate info."""
        return f"{self.resolution[0]}x{self.resolution[1]}@{round(self.fps, ndigits=3)}"
