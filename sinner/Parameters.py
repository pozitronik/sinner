import glob
import os
import platform
from argparse import ArgumentParser, Namespace
from typing import List

from sinner.processors.BaseValidatedClass import BaseValidatedClass, Rules
from sinner.utilities import list_class_descendants, resolve_relative_path, get_app_dir, TEMP_DIRECTORY


class Parameters(BaseValidatedClass):
    SIGNATURE: str = 'def register_arguments(args: List[str]) -> None'
    parser: ArgumentParser = ArgumentParser()
    parameters: Namespace

    def rules(self) -> Rules:
        return [
            {'parameter': 'frame-processor', 'type': List[str], 'required': True},
            {'parameter': 'frame-processor', 'default': ['FaceSwapper']},
            {'parameter': 'frame-processor', 'choices': list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor')},
            {'parameter': 'frame-handler', 'type': str, 'choices': list_class_descendants(resolve_relative_path('handlers/frame'), 'BaseFrameHandler')},
            {'parameter': 'max-memory', 'type': int, 'default': self.suggest_max_memory()},
            {'parameter': 'gui', 'type': bool, 'default': False, 'action': True},
            {'parameter': 'benchmark', 'type': bool, 'default': False, 'action': True},
            {'parameter': 'temp-dir', 'type': str | None, 'default': None},
            {'parameter': 'temp-dir', 'type': str | None, 'default': None},
        ]

    def __init__(self):
        args, unknown_args = self.parser.parse_known_args()
        for argument in unknown_args:
            key, value = self.parse_argument(argument)
            setattr(args, key, value)
        self.parameters = args
        if not self.load(self.parameters):
            self.write_errors()
            quit()

    def list_modules(self) -> List[str]:
        module_files = glob.glob('*.py', recursive=True)
        modules = []
        for file in module_files:
            if self.acceptable_for_loading(file):
                modules.append(file)
        return modules

    def acceptable_for_loading(self, file_path: str):
        with open(file_path, 'r') as file:
            for line in file:
                if self.SIGNATURE in line:
                    return True
        return False

    @staticmethod
    def parse_argument(argument: str) -> tuple[str, str] | tuple[str, list[str]] | None:  # key and list of values
        if not argument.startswith('--'):
            return None
        if '=' in argument:  # '--key=value'
            key, value = argument[2:].split('=')
            return key, value
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
