import vlc
from argparse import Namespace

from sinner.models.audio.BaseAudioBackend import BaseAudioBackend


class VLCAudioBackend(BaseAudioBackend):
    _position: int | None = None
    _show_player_window: bool = True

    _vlc_instance: vlc.Instance

    def __init__(self, parameters: Namespace, media_path: str | None = None) -> None:
        super().__init__(parameters, media_path)
        self._vlc_instance = vlc.Instance() if self._show_player_window else vlc.Instance(['--intf=dummy', '--no-video'])
        self._player = self._vlc_instance.media_player_new(uri=media_path) if media_path else self._vlc_instance.media_player_new

    @property
    def volume(self) -> int:
        return self._player.audio_get_volume()

    @volume.setter
    def volume(self, vol: int) -> None:
        self._player.audio_set_volume(vol)

    @property
    def position(self) -> int | None:
        pos = self._player.get_time()
        if pos == -1:  # Indicates that the position is not available
            return None
        return pos * 1000  # Convert to seconds

    @position.setter
    def position(self, position: int) -> None:
        self._position = position
        self._player.set_time(position * 1000)

    def play(self) -> None:
        self._player.play()
        if self._position is not None:
            self._player.set_time(self._position * 1000)
            self._position = None

    def pause(self) -> None:
        self._player.pause()  # VLC's pause function toggles pause, so this method can also unpause

    def stop(self) -> None:
        self._player.stop()

    def unpause(self) -> None:
        if self._player.is_playing():
            self._player.pause()  # Toggle pause to unpause if currently paused
