import os
import platform
import shlex
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from sinner.processors.BaseValidatedClass import BaseValidatedClass, Rules
from sinner.utilities import list_class_descendants, resolve_relative_path, get_app_dir, TEMP_DIRECTORY


class Parameters(BaseValidatedClass):
    frame_processor: List[str] = None
    frame_handler: str = None
    max_memory: int = None
    gui: bool = False
    benchmark: bool = True
    temp_dir: str | None = None

    parser: ArgumentParser = ArgumentParser()
    parameters: Namespace

    def rules(self) -> Rules:
        return [
            {'parameter': 'frame-processor', 'default': ['FaceSwapper'], 'required': True, 'choices': list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor')},
            {'parameter': 'frame-handler', 'choices': list_class_descendants(resolve_relative_path('handlers/frame'), 'BaseFrameHandler')},
            {'parameter': 'max-memory', 'default': self.suggest_max_memory()},
            {'parameter': 'gui', 'default': False},
            {'parameter': 'benchmark', 'default': False},
            {'parameter': 'temp-dir', 'default': None}
        ]

    def __init__(self, command_line: str | None = None):
        self.parameters = self.command_line_to_namespace(command_line)
        if not self.load(self.parameters):
            self.write_errors()
            quit()

    @staticmethod
    def command_line_to_namespace(cmd_params: str | None = None) -> Namespace:
        processed_parameters: Namespace = Namespace()
        if cmd_params is None:
            args_list = sys.argv[1:]
        else:
            args_list = shlex.split(cmd_params)
        result = []
        current_sublist = []
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
            else:
                key, value = parameter[0].split('=')
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
            value = value.split()
            return key, value

    @staticmethod
    def suggest_max_memory() -> int:
        if platform.system().lower() == 'darwin':
            return 4
        return 16

    def suggest_temp_dir(self, temp_dir: str | None) -> str:
        if self.parameters.benchmark:
            return ''
        return temp_dir if temp_dir is not None else os.path.join(os.path.dirname(self.parameters.target_path), get_app_dir(), TEMP_DIRECTORY)
