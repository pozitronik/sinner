import glob
import os
import shutil
from argparse import Namespace

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.Parameters import Parameters
from sinner.State import State
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.processors.frame.FrameExtractor import FrameExtractor
from tests.constants import tmp_dir, target_mp4, TARGET_FC

parameters: Namespace = Parameters(f'--target-path="{target_mp4}" --output-path="{tmp_dir}"').parameters


def setup():
    #  clean previous results, if exists
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def test_extract() -> None:
    assert os.path.exists(tmp_dir) is False
    batch_processor = BatchProcessingCore(parameters=parameters)
    handler = batch_processor.suggest_handler(batch_processor.target_path, batch_processor.parameters)

    test_extractor = FrameExtractor(parameters=parameters)
    test_state = State(
        parameters=parameters,
        frames_count=TARGET_FC,
        temp_dir=tmp_dir,
        processor_name=test_extractor.__class__.__name__,
        target_path=target_mp4
    )
    batch_processor.process(test_extractor, handler, test_state)
    assert os.path.exists(tmp_dir) is True
    assert len(glob.glob(os.path.join(glob.escape(test_state.path), '*.png'))) == TARGET_FC
