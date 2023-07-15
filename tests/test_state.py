import os.path
import shutil
from argparse import Namespace

from sinner.Parameters import Parameters
from sinner.State import State
from tests.constants import tmp_dir, target_mp4, source_jpg

parameters: Namespace = Parameters(f'--frame-processor=DummyProcessor --source-path="{source_jpg}" --target-path="{target_mp4}" --output-path="{tmp_dir}"').parameters


def setup_function():
    setup()


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def test() -> None:
    state = State(parameters=Namespace(), target_path=None, temp_dir='data/temp', frames_count=0, processor_name='')

    assert os.path.exists('data/temp/IN') is False
    assert os.path.exists('data/temp/OUT') is False
    assert state.source_path is None
    assert state.target_path is None
    assert state._temp_dir == os.path.normpath('data/temp')
    assert state.in_dir == os.path.normpath('data/temp/IN')
    assert state.out_dir == os.path.normpath('data/temp/OUT')

    assert os.path.exists('data/temp/IN') is True
    assert os.path.exists('data/temp/OUT') is True

    assert state.is_started is False
    assert state.is_finished is False
