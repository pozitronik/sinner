from colorama import Fore, Back, Style


class LoaderException(Exception):
    message: str
    validated_object: object
    attribute: str

    def __init__(self, message: str, validated_object: object, attribute: str):
        self.message = message
        self.validated_object = validated_object
        self.attribute = attribute

    def __str__(self) -> str:
        return f"{Fore.BLACK}{Back.RED}{self.validated_object.__class__.__name__}{Back.RESET}{Fore.RESET}: {self.message}@{Style.BRIGHT}{self.attribute}{Style.RESET_ALL}"
