from typing import Type, List, Dict

from sinner.Core import Core
from sinner.validators import AttributeLoader

DocumentedClasses: List[Type[AttributeLoader]] = [
    Core
]


class AttributeDocumenter:

    def show_help(self):
        print(self.collect())
        quit()

    @staticmethod
    def collect():
        collected_doc: List[Dict[str, List[Dict[str, str]]]] = []
        for doc_class in DocumentedClasses:
            class_doc: List[Dict[str, str]] = []

            loaded_class: Type[AttributeLoader] = doc_class()
            loadable_attributes = loaded_class.validating_attributes()
            for attribute in loadable_attributes:
                help_string = loaded_class.get_attribute_help()
                class_doc.append({attribute: help_string})
            collected_doc.append({doc_class: class_doc})
        return collected_doc
