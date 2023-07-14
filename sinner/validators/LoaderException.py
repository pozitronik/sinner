import os
from typing import List

from colorama import Fore, Back, Style


# The exception inside a loader
class LoaderException(Exception):
    message: str
    validated_object: object
    attribute: str

    def __init__(self, message: str, validated_object: object, attribute: str):
        self.message = message
        self.validated_object = validated_object
        self.attribute = attribute

    def __str__(self) -> str:
        return f"{Fore.BLACK}{Back.RED}{self.validated_object.__class__.__name__}{Back.RESET}{Fore.RESET}: {self.message} ({Style.BRIGHT}{self.attribute}{Style.RESET_ALL})"


# The user exception, when loading is not success
class LoadingException(Exception):
    errors: List[dict[str, str]] = []

    def __init__(self, errors: List[dict[str, str]]):
        self.errors = errors

    def __str__(self) -> str:
        validation_errors: List[str] = []
        attributes_help: List[str] = []
        for error in self.errors:
            validation_errors.append(f"Parameter {Fore.YELLOW}--{error['attribute']}{Fore.RESET}{Fore.RED} {error['error']}{Fore.RESET} {Fore.WHITE}in module{Fore.RESET} {Fore.CYAN}{error['module']}{Fore.RESET}")
            if error['help'] is not None:
                attributes_help.append(f"{Style.BRIGHT}{Fore.YELLOW}--{error['attribute']}{Fore.RESET}={error['help']}{Style.RESET_ALL}")
            else:
                attributes_help.append(f"{Style.BRIGHT}{Fore.YELLOW}--{error['attribute']}{Fore.RESET}{Style.RESET_ALL}")
        return os.linesep.join(validation_errors) + os.linesep + ' '.join(attributes_help)
