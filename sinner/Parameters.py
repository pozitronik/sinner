import platform
import shlex
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from sinner.validators.AttributeLoader import AttributeLoader, Rules
from sinner.utilities import list_class_descendants, resolve_relative_path


class Parameters(AttributeLoader):
    gui: bool
    benchmark: str | None = None
    max_memory: int

    parser: ArgumentParser = ArgumentParser()
    parameters: Namespace

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'max-memory',
                'default': self.suggest_max_memory()
            },
            {
                'parameter': 'gui',
                'default': False
            },
            {
                'parameter': 'benchmark',
                'default': None,
                'choices': list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor')
            },
        ]

    def __init__(self, command_line: str | None = None):
        self.parameters = self.command_line_to_namespace(command_line)
        super().__init__(self.parameters)
        self.parameters.max_memory = self.max_memory  # add initialized value to use it later

    @staticmethod
    def command_line_to_namespace(cmd_params: str | None = None) -> Namespace:
        processed_parameters: Namespace = Namespace()
        if cmd_params is None:
            args_list = sys.argv[1:]
        else:
            args_list = shlex.split(cmd_params)
        result = []
        current_sublist: List[str] = []
        for item in args_list:
            if item.startswith('--'):
                if current_sublist:
                    result.append(current_sublist)
                    current_sublist = []
                current_sublist.append(item)
            else:
                current_sublist.append(item)
        if current_sublist:
            result.append(current_sublist)

        for parameter in result:
            if len(parameter) > 2:
                setattr(processed_parameters, parameter[0].lstrip('-'), parameter[1:])
            elif len(parameter) == 1 and '=' not in parameter[0]:
                setattr(processed_parameters, parameter[0].lstrip('-'), True)
            else:  # 2 args
                key, value = parameter[0].split('=') if '=' in parameter[0] else parameter
                setattr(processed_parameters, key.lstrip('-'), value)
        return processed_parameters

    @staticmethod
    def parse_argument(argument: str) -> tuple[str, str] | tuple[str, list[str]] | None:  # key and list of values
        if not argument.startswith('--'):
            return None
        if '=' in argument:  # '--key=value'
            key, value = argument[2:].split('=')
            return key, value
        elif ' ' not in argument:  # --key
            return None
        else:  # '--key value1 value2'
            key, value = argument[2:].split('=')
            return key, value.split()

    @staticmethod
    def suggest_max_memory() -> int:
        if platform.system().lower() == 'darwin':
            return 4
        return 16
