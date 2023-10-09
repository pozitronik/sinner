from argparse import Namespace
from typing import List, Tuple

from sinner.Status import Status, Mood
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import Frame
from sinner.utilities import list_class_descendants, resolve_relative_path
from sinner.validators.AttributeLoader import Rules


class GUIProcessingCore(Status):
    frame_processor: List[str]

    parameters: Namespace
    preview_processors: dict[str, BaseFrameProcessor]  # cached processors for gui
    preview_handlers: dict[str, BaseFrameHandler]  # cached handlers for gui

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
                'module_help': 'The GUI processing handler'
            }
        ]

    def __init__(self, parameters: Namespace):
        self.parameters = parameters
        self.preview_processors = {}
        super().__init__(parameters)

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
