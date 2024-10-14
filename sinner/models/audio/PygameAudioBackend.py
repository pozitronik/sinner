import os.path
import tempfile
from argparse import Namespace

from moviepy.editor import AudioFileClip
import pygame

from sinner.models.status.Mood import Mood
from sinner.models.audio.BaseAudioBackend import BaseAudioBackend
from sinner.utilities import get_file_name, normalize_path


class PygameAudioBackend(BaseAudioBackend):
    _clip: AudioFileClip | None = None
    _temp_dir: str
    _audio_path: str
    _media_loaded: bool = False
    _media_is_playing: bool = False
    _position: int | None = None

    def __init__(self, parameters: Namespace, media_path: str | None = None) -> None:
        self._temp_dir = os.path.abspath(os.path.join(os.path.normpath(vars(parameters).get('temp_dir', tempfile.gettempdir())), 'extracted_audio'))
        os.makedirs(self._temp_dir, exist_ok=True)
        pygame.mixer.init()
        super().__init__(parameters, media_path)

    @property
    def media_path(self) -> str | None:
        return self._media_path

    @media_path.setter
    def media_path(self, media_path: str) -> None:
        self._media_path = str(normalize_path(media_path))
        self.update_status(f"Using audio backend for {self._media_path}")
        self._clip = AudioFileClip(self.media_path)
        self._audio_path = os.path.join(self._temp_dir, get_file_name(self.media_path) + '.wav')  # type: ignore[arg-type]  # self._media_path always have a value here
        if not os.path.exists(self._audio_path):
            try:
                self._clip.write_audiofile(self._audio_path, codec='pcm_s32le')
            except Exception as exception:
                self.update_status(message=f"Unable to save the temp audio. Possible reasons: no audio in the media/no access rights/no space on device. \n {str(exception)}", mood=Mood.BAD)
                return
        try:
            pygame.mixer.music.load(self._audio_path)
            self._media_loaded = True
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)

    def play(self) -> None:
        """Plays the loaded media from the current position."""
        if self._media_loaded and not self._media_is_playing:
            pygame.mixer.music.play()
            self._media_is_playing = True
            if self._position is not None:
                pygame.mixer.music.set_pos(self._position)
                self._position = None

    def stop(self) -> None:
        """Stops playback."""
        if self._media_is_playing:
            pygame.mixer.music.stop()
            self._media_is_playing = False

    def pause(self) -> None:
        """Pauses playback."""
        pygame.mixer.music.pause()

    def unpause(self) -> None:
        """Resumes playback."""
        pygame.mixer.music.unpause()

    @property
    def volume(self) -> int:
        return int(pygame.mixer.music.get_volume() * 100)

    @volume.setter
    def volume(self, vol: int) -> None:
        pygame.mixer.music.set_volume(vol / 100)

    @property
    def position(self) -> int | None:
        return None

    @position.setter
    def position(self, position: int) -> None:
        self._position = position
        if self._media_is_playing:
            pygame.mixer.music.set_pos(self._position)
            self._position = None
