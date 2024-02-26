import os.path
import tempfile
from argparse import Namespace

from moviepy.editor import AudioFileClip
import pygame

from sinner.Status import Mood
from sinner.models.audio.BaseAudioBackend import BaseAudioBackend
from sinner.utilities import get_file_name


class PygameAudioBackend(BaseAudioBackend):
    _clip: AudioFileClip | None = None
    _temp_dir: str
    _audio_path: str
    _media_loaded: bool = False

    def __init__(self, parameters: Namespace, media_path: str | None) -> None:
        super().__init__(parameters, media_path)
        self._temp_dir = os.path.abspath(os.path.join(os.path.normpath(vars(parameters).get('temp_dir', tempfile.gettempdir())), 'extracted_audio'))
        pygame.mixer.init()

    @property
    def media_path(self) -> str | None:
        return self._media_path

    @media_path.setter
    def media_path(self, media_path: str) -> None:
        super().media_path = media_path
        self._clip = AudioFileClip(self.media_path)
        self._audio_path = os.path.join(self._temp_dir, get_file_name(self.media_path), '.wav')
        if not os.path.exists(self._audio_path):
            self.clip.write_audiofile(self._audio_path, codec='pcm_s16le')
        try:
            pygame.mixer.music.load(self._audio_path)
            self._media_loaded = True
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)

    def play(self):
        """Plays the loaded media from the current position."""
        if self._media_loaded:
            pygame.mixer.music.play()

    def set_volume(self, volume):
        """Sets the playback volume."""
        self.volume = volume
        pygame.mixer.music.set_volume(volume)

    def stop(self):
        """Stops playback."""
        pygame.mixer.music.stop()
        self._media_loaded = False

    def pause(self):
        """Pauses playback."""
        pygame.mixer.music.pause()

    def unpause(self):
        """Resumes playback."""
        pygame.mixer.music.unpause()

    @property
    def volume(self) -> int:
        return int(pygame.mixer.music.get_volume() * 100)

    @volume.setter
    def volume(self, vol: int) -> None:
        super().volume = vol
        pygame.mixer.music.set_volume(self.volume / 100)

    @property
    def position(self) -> int | None:
        return None

    @position.setter
    def position(self, position: int) -> None:
        pygame.mixer.music.set_pos(position)

# Example usage
# audio_backend = PygameAudioBackend()
# audio_backend.load_media('path/to/your/media.mp3', start_time=10)  # Load media and seek to 10 seconds
# audio_backend.set_volume(0.8)  # Set volume
# audio_backend.play()
