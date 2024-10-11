import os.path
from abc import ABC, abstractmethod
from typing import List, Any, Callable

from argparse import Namespace

from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.models.State import State
from sinner.validators.AttributeLoader import Rules, AttributeLoader
from sinner.typing import Frame
from sinner.utilities import load_class, suggest_execution_providers, decode_execution_providers


class BaseFrameProcessor(ABC, AttributeLoader):
    execution_provider: List[str]
    self_processing: bool = False

    parameters: Namespace

    @staticmethod
    def create(processor_name: str, parameters: Namespace) -> 'BaseFrameProcessor':  # processors factory
        handler_class = load_class(os.path.dirname(__file__), processor_name)

        if handler_class and issubclass(handler_class, BaseFrameProcessor):
            params: dict[str, Any] = {'parameters': parameters}
            return handler_class(**params)
        else:
            raise ValueError(f"Invalid processor name: {processor_name}")

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'execution-provider',
                'required': True,
                'default': ['cpu'],
                'choices': suggest_execution_providers(),
                'help': 'The execution provider, from available on your hardware/software'
            }
        ]

    def __init__(self, parameters: Namespace) -> None:
        self.parameters = parameters
        super().__init__(self.parameters)

    @abstractmethod
    def process_frame(self, frame: Frame) -> Frame:
        pass

    def release_resources(self) -> None:
        pass

    def configure_state(self, state: State) -> None:
        pass

    @property
    def execution_providers(self) -> List[str]:
        return decode_execution_providers(self.execution_provider)

    def configure_output_filename(self, callback: Callable[[str], None]) -> None:
        pass

    def process(self, handler: BaseFrameHandler, state: State) -> None:
        pass
