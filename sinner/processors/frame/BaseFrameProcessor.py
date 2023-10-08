import os.path
from abc import ABC, abstractmethod
from typing import List, Any

from argparse import Namespace

from sinner.State import State
from sinner.Status import Status
from sinner.validators.AttributeLoader import Rules
from sinner.typing import Frame
from sinner.utilities import load_class, suggest_execution_threads, suggest_execution_providers, decode_execution_providers


class BaseFrameProcessor(ABC, Status):
    execution_provider: List[str]
    execution_threads: int

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
        return super().rules() + [
            {
                'parameter': 'execution-provider',
                'required': True,
                'default': ['cpu'],
                'choices': suggest_execution_providers(),
                'help': 'The execution provider, from available on your hardware/software'
            },
            {
                'parameter': 'execution-threads',
                'type': int,
                'default': suggest_execution_threads(),
                'help': 'The count of simultaneous processing threads'
            },
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
