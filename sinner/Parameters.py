import glob
from argparse import ArgumentParser, Namespace
from typing import List

from sinner.utilities import list_class_descendants, resolve_relative_path


class Parameters:
    SIGNATURE: str = 'def register_arguments(args: List[str]) -> None'
    parser: ArgumentParser = ArgumentParser(prog='😈sinner')
    parameters: Namespace

    def __init__(self):
        self.init_main_arguments()
        args, unknown_args = self.parser.parse_known_args()
        for argument in unknown_args:
            key, value = self.parse_argument(argument)
            setattr(args, key, value)
        self.parameters = args

    def validate(self):
        pass

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


def init_main_arguments(self):
    self.parser.add_argument('--frame-processor', help='pipeline of frame processors', dest='frame_processor', default=['FaceSwapper'],
                             choices=list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor'), nargs='+')
