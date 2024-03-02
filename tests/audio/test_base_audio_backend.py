import os
from argparse import Namespace

import pytest

from sinner.Parameters import Parameters
from sinner.models.audio import PygameAudioBackend
from sinner.models.audio.BaseAudioBackend import BaseAudioBackend
from sinner.models.audio.VLCAudioBackend import VLCAudioBackend
from tests.constants import target_mp4

parameters: Namespace = Parameters().parameters


def test_audio_backend_factory() -> None:
    if 'CI' in os.environ:
        pytest.skip("Sound can not be initialized in GitHub CI")
    assert (BaseAudioBackend.create(backend_name='PygameAudioBackend', parameters=parameters, media_path=target_mp4), PygameAudioBackend)
    assert (BaseAudioBackend.create(backend_name='VLCAudioBackend', parameters=parameters, media_path=target_mp4), VLCAudioBackend)
    with pytest.raises(Exception):
        BaseAudioBackend.create(backend_name='UnknownBackend', parameters=parameters, media_path=target_mp4)


def test_audio_backend_list() -> None:
    backends = BaseAudioBackend.list()
    assert 'PygameAudioBackend' in backends
    assert 'VLCAudioBackend' in backends
    assert 2 == len(backends)
