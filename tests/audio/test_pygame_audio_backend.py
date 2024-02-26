import os.path
import tempfile
from argparse import Namespace
from tests.constants import tmp_dir, target_mp4
from sinner.Parameters import Parameters
from sinner.models.audio.PygameAudioBackend import PygameAudioBackend


def test_init_default() -> None:
    params: Namespace = Parameters().parameters
    backend = PygameAudioBackend(params)
    assert backend.media_path is None
    assert backend._temp_dir == os.path.join(tempfile.gettempdir(), 'extracted_audio')


def test_init_parameters() -> None:
    params: Namespace = Parameters(f'--temp_dir={tmp_dir}').parameters
    backend = PygameAudioBackend(params, target_mp4)
    assert backend._temp_dir == tmp_dir
    assert backend.media_path is os.path.join(tmp_dir, 'extracted_audio', 'target.wav')
    assert os.path.exists(backend.media_path)
