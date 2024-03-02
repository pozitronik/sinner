import vlc
from argparse import Namespace

from sinner.models.audio.BaseAudioBackend import BaseAudioBackend


class VLCAudioBackend(BaseAudioBackend):
    def __init__(self, parameters: Namespace, media_path: str | None = None) -> None:
        super().__init__(parameters, media_path)
        self._player = vlc.MediaPlayer(media_path) if media_path else vlc.MediaPlayer()
        self._vlc_instance = vlc.Instance()

    @property
    def volume(self) -> int:
        return self._player.audio_get_volume()

    @volume.setter
    def volume(self, vol: int) -> None:
        self._player.audio_set_volume(vol)

    @property
    def position(self) -> int | None:
        pos = self._player.get_position()
        if pos == -1:  # Indicates that the position is not available
            return None
        return int(self._player.get_length() * pos)  # Convert to seconds

    @position.setter
    def position(self, position: int) -> None:
        self._player.set_position(position / self._player.get_length())

    def play(self) -> None:
        self._player.play()

    def pause(self) -> None:
        self._player.pause()  # VLC's pause function toggles pause, so this method can also unpause

    def stop(self) -> None:
        self._player.stop()

    def unpause(self) -> None:
        if self._player.is_playing():
            self._player.pause()  # Toggle pause to unpause if currently paused
