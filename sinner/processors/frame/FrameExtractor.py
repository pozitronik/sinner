import os
from argparse import Namespace

from tqdm import tqdm

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.models.State import State
from sinner.typing import Frame
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor


class FrameExtractor(BaseFrameProcessor):
    emoji: str = '🏃'
    self_processing: bool = True

    def rules(self) -> Rules:
        return [
            {
                'module_help': 'This module extracts frames from video file as a set of png images'
            }
        ]

    def configure_state(self, state: State) -> None:
        state.path = os.path.abspath(os.path.join(state.temp_dir, self.__class__.__name__, str(os.path.basename(str(state.target_path)))))

    def process_frame(self, frame: Frame) -> Frame:
        return frame

    def process(self, handler: BaseFrameHandler, state: State) -> None:
        handler.get_frames_paths(path=state.path, frames_range=(state.processed_frames_count, None))
        _, lost_frames = state.final_check()
        if lost_frames:
            with tqdm(
                    total=len(lost_frames),
                    desc="Processing lost frames", unit='frame',
                    dynamic_ncols=True,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
            ) as progress:
                for frame_index in lost_frames:
                    state.save_temp_frame(handler.extract_frame(frame_index))
                    progress.update()

        is_ok, _ = state.final_check()
        if not is_ok:
            raise Exception("Something went wrong on processed frames check")
