import os.path

from moviepy.editor import AudioFileClip
import pygame
import threading

from sinner.utilities import get_file_name


class PygameAudioBackend:
    def __init__(self):
        pygame.mixer.init()
        self.clip = None
        self.volume = 0.5  # Default volume (0 to 1)

    def load_media(self, path, start_time=0):
        """Loads media and seeks to the specified position."""
        # Use moviepy to load the audio clip (works with audio and video files)
        self.clip = AudioFileClip(path)
        # Seek to the start_time if specified (moviepy handles this)
        if start_time:
            self.clip = self.clip.subclip(start_time)

        # Save the audio segment to a temporary file (pygame workaround for playback)
        temp_audio_path = get_file_name(path)+'.wav'
        if not os.path.exists(temp_audio_path):
            self.clip.write_audiofile(temp_audio_path, codec='pcm_s16le')

        # Load the temporary audio file with pygame for playback
        pygame.mixer.music.load(temp_audio_path)
        pygame.mixer.music.set_volume(self.volume)

    def play(self):
        """Plays the loaded media from the current position."""
        if self.clip:
            pygame.mixer.music.play()

    def set_volume(self, volume):
        """Sets the playback volume."""
        self.volume = volume
        pygame.mixer.music.set_volume(volume)

    def stop(self):
        """Stops playback."""
        pygame.mixer.music.stop()

    def pause(self):
        """Pauses playback."""
        pygame.mixer.music.pause()

    def unpause(self):
        """Resumes playback."""
        pygame.mixer.music.unpause()


# Example usage
# audio_backend = PygameAudioBackend()
# audio_backend.load_media('path/to/your/media.mp3', start_time=10)  # Load media and seek to 10 seconds
# audio_backend.set_volume(0.8)  # Set volume
# audio_backend.play()
