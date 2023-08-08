from typing import Type, List, Dict

from colorama import Style, Fore

from sinner.Benchmark import Benchmark
from sinner.Core import Core
from sinner.Preview import Preview
from sinner.State import State
from sinner.Status import Status
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.FFmpegVideoHandler import FFmpegVideoHandler
from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.processors.frame.FaceEnhancer import FaceEnhancer
from sinner.processors.frame.FaceSwapper import FaceSwapper
from sinner.processors.frame.FrameExtractor import FrameExtractor
from sinner.processors.frame.FrameResizer import FrameResizer
from sinner.processors.frame.ResultProcessor import ResultProcessor
from sinner.validators import AttributeLoader

DocumentedClasses: List[Type[AttributeLoader]] = [
    Core,
    Status,
    State,
    Preview,
    Benchmark,
    FaceEnhancer,
    FaceSwapper,
    FrameExtractor,
    FrameResizer,
    ResultProcessor,
    CV2VideoHandler,
    DirectoryHandler,
    FFmpegVideoHandler,
    ImageHandler,
    VideoHandler
]


class AttributeDocumenter:

    def show_help(self):
        raw_help_doc = self.collect()
        help_doc = self.format(raw_help_doc)
        print(help_doc)
        quit()

    @staticmethod
    def collect() -> List[Dict[str, List[Dict[str, str]]]]:
        collected_doc: List[Dict[str, List[Dict[str, str]]]] = []
        for doc_class in DocumentedClasses:
            class_doc: List[Dict[str, str]] = []
            loaded_class: Type[AttributeLoader] = doc_class.__new__(doc_class)
            loadable_attributes = loaded_class.validating_attributes()
            for attribute in loadable_attributes:
                help_string = loaded_class.get_attribute_help(attribute)
                class_doc.append({attribute: help_string})
            module_help = loaded_class.get_module_help()
            collected_doc.append({'module': doc_class.__name__, 'module_help': module_help, 'attributes': class_doc})
        return collected_doc

    @staticmethod
    def format(raw_help_doc: List[Dict[str, List[Dict[str, str]]]]) -> str:
        result: str = ''
        for module_data in raw_help_doc:
            module_help = f"{Style.DIM}<No help provided>{Fore.RESET}" if module_data['module_help'] is None else module_data['module_help']
            result += f'{Style.BRIGHT}{Fore.BLUE}{module_data["module"]}{Fore.RESET}{Style.RESET_ALL}: {module_help[:1].lower() + module_help[1:]}\n'
            for attribute in module_data['attributes']:
                for name, value in attribute.items():
                    help_str: str = f"{Style.DIM}<No help provided>{Fore.RESET}" if value is None else value
                    result += f'\t{Style.BRIGHT}{Fore.YELLOW}--{name}{Fore.RESET}{Style.RESET_ALL}: {help_str}\n'
        return result
