from dataclasses import dataclass
from typing import Tuple, Dict, Any


@dataclass
class MediaMetaData:
    """
    Data class for storing media metadata and parameters.
    """
    resolution: Tuple[int, int] = (0, 0)  # (width, height)
    render_resolution: Tuple[int, int] = (0, 0)  # The resolution, frame rendered with
    fps: float = 0  # Frames per second, 0 as infinite value
    frames_count: int = 0  # Total number of frames

    @property
    def length(self) -> float:
        """
        Calculate video length in seconds.

        Returns:
            float: Media duration in seconds, if applicable, 1 for non-playable media
        """
        return self.frames_count / self.fps if self.fps > 0 else 1

    @property
    def frame_time(self) -> float:
        """
        Calculate frame time in seconds.

        Returns:
            float: Frame time in seconds, if applicable, none for non-playable media
        """
        return 1 / self.fps if self.fps > 0 else 1

    def get_formatted_length(self) -> str:
        """
        Get formatted media length as HH:MM:SS.

        Returns:
            str: Formatted media duration
        """
        if self.length:
            total_seconds = int(self.length)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return "Non-playable media"

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

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в обычный словарь"""
        return {
            "render_resolution": self.render_resolution,
            "resolution": self.resolution,
            "fps": self.fps,
            "frames_count": self.frames_count
        }
