import pytest

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.FFmpegVideoHandler import FFmpegVideoHandler
from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from tests.constants import target_mp4, state_frames_dir, target_png


def test_handlers_factory() -> None:
    assert (BaseFrameHandler.create(handler_name='CV2VideoHandler', target_path=target_mp4), CV2VideoHandler)
    assert (BaseFrameHandler.create(handler_name='FFmpegVideoHandler', target_path=target_mp4), FFmpegVideoHandler)
    assert (BaseFrameHandler.create(handler_name='VideoHandler', target_path=target_mp4), VideoHandler)
    assert (BaseFrameHandler.create(handler_name='DirectoryHandler', target_path=state_frames_dir), DirectoryHandler)
    assert (BaseFrameHandler.create(handler_name='ImageHandler', target_path=target_png), ImageHandler)
    with pytest.raises(Exception):
        BaseFrameHandler.create(handler_name='UnknownHandler', target_path=target_png)
