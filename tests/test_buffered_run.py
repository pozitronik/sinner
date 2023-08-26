import os

from sinner.Core import Core
from sinner.Parameters import Parameters
from tests.constants import source_target_mp4_result, target_mp4, source_jpg
from tests.test_run import threads_count


def test_buffered_run() -> None:
    params = Parameters(f'--target-path="{target_mp4}" --source-path="{source_jpg}" --execution-treads={threads_count}  --frame-processor FaceSwapper FaceEnhancer')
    Core(parameters=params.parameters).buffered_run()