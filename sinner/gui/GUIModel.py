import queue
import threading
from argparse import Namespace
from typing import List, Tuple

from sinner.Status import Status, Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import list_class_descendants, resolve_relative_path
from sinner.validators.AttributeLoader import Rules


class GUIModel(Status):
    frame_processor: List[str]
    source_path: str
    target_path: str

    parameters: Namespace
    preview_processors: dict[str, BaseFrameProcessor]  # cached processors for gui
    preview_handlers: dict[str, BaseFrameHandler]  # cached handlers for gui

    _extractor_handler: BaseFrameHandler | None = None
    _previews: dict[int, List[Tuple[Frame, str]]] = {}  # position: [frame, caption]
    _current_frame: Frame | None
    _processing_thread: threading.Thread
    _viewing_thread: threading.Thread
    _frames_queue: queue.PriorityQueue[tuple[int, Frame]]
    _frame_wait_time: float = 0
    _processors: List[BaseFrameProcessor] = []
    _is_playing: bool = False
    _fps: float  # playing fps

    frame_processor: List[str]

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'frame-processor', 'processor', 'processors'},
                'attribute': 'frame_processor',
                'default': ['FaceSwapper'],
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('../processors/frame'), 'BaseFrameProcessor'),
                'help': 'The set of frame processors to handle the target'
            },
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path'
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path'
            },
            {
                'module_help': 'The GUI processing handler'
            }
        ]

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        self.preview_processors = {}
        super().__init__(parameters)
        self._frames_queue = queue.PriorityQueue()

    #  returns list of all processed frames, starting from the original
    def get_frame(self, frame_number: int, extractor_handler: BaseFrameHandler, processed: bool = False) -> List[Tuple[Frame, str]]:
        result: List[Tuple[Frame, str]] = []
        try:
            _, frame, _ = extractor_handler.extract_frame(frame_number)
            result.append((frame, 'Original'))
        except Exception as exception:
            self.update_status(message=str(exception), mood=Mood.BAD)
            return result
        if processed:  # return processed frame
            try:
                for processor_name in self.frame_processor:
                    if processor_name not in self.preview_processors:
                        self.preview_processors[processor_name] = BaseFrameProcessor.create(processor_name, self.parameters)
                    self.preview_processors[processor_name].load(self.parameters)
                    frame = self.preview_processors[processor_name].process_frame(frame)
                    result.append((frame, processor_name))
            except Exception as exception:  # skip, if parameters is not enough for processor
                self.update_status(message=str(exception), mood=Mood.BAD)
                pass
        return result
