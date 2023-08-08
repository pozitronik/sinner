from typing import Type, List, Dict

from colorama import Style, Fore

from sinner.Core import Core
from sinner.validators import AttributeLoader

DocumentedClasses: List[Type[AttributeLoader]] = [
    Core
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
            collected_doc.append({doc_class.__name__: class_doc})
        return collected_doc

    @staticmethod
    def format(raw_help_doc: List[Dict[str, List[Dict[str, str]]]]) -> str:
        result: str = ''
        for module_help in raw_help_doc:
            for module_name, attributes in module_help.items():
                result += f'{Style.BRIGHT}{Fore.BLUE}{module_name}{Fore.RESET}{Style.RESET_ALL}:\n'
                for attribute in attributes:
                    for name, value in attribute.items():
                        help_str: str = f"{Style.DIM}<No help provided>{Fore.RESET}" if value is None else value
                        result += f'\t{Style.BRIGHT}{Fore.YELLOW}--{name}{Fore.RESET}{Style.RESET_ALL}: {help_str}\n'
        return result
