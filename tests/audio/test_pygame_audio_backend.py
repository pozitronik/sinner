import os.path
import shutil
import tempfile
from argparse import Namespace

import pygame
import pytest

from tests.constants import tmp_dir, target_mp4, silent_target_mp4
from sinner.Parameters import Parameters
from sinner.models.audio.PygameAudioBackend import PygameAudioBackend


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def setup_function():
    setup()


def teardown_function():
    pygame.mixer.quit()
    pygame.quit()


@pytest.mark.skipif('CI' in os.environ, reason="Sound can not be initialized in GitHub CI")
def test_init_default() -> None:
    params: Namespace = Parameters().parameters
    backend = PygameAudioBackend(params)
    assert backend.media_path is None
    assert backend._temp_dir == os.path.join(tempfile.gettempdir(), 'extracted_audio')


@pytest.mark.skipif('CI' in os.environ, reason="Sound can not be initialized in GitHub CI")
def test_init_parameters() -> None:
    params: Namespace = Parameters(f'--temp_dir="{tmp_dir}"').parameters
    backend = PygameAudioBackend(params, target_mp4)
    assert backend._temp_dir == os.path.join(tmp_dir, 'extracted_audio')
    assert backend._audio_path == os.path.join(tmp_dir, 'extracted_audio', 'target.wav')
    assert os.path.exists(backend.media_path)


@pytest.mark.skip(reason="Not ready due to issues with PygameAudioBackend")
def test_on_silent(capsys) -> None:
    params: Namespace = Parameters(f'--temp_dir="{tmp_dir}"').parameters
    PygameAudioBackend(params, silent_target_mp4)
    captured = capsys.readouterr()
    assert "Unable to save the temp audio" in captured.out
