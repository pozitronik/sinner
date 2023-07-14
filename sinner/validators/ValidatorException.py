from colorama import Fore, Back, Style


class ValidatorException(Exception):
    message: str
    validated_object: object
    validator_object: object

    def __init__(self, message: str, validated_object: object, validator_object: object):
        self.message = message
        self.validated_object = validated_object
        self.validator_object = validator_object

    def __str__(self) -> str:
        return f"{Fore.BLACK}{Back.RED}{self.validator_object.__class__.__name__}{Back.RESET}{Fore.RESET}: {self.message}@{Style.BRIGHT}{self.validated_object.__class__.__name__}{Style.RESET_ALL}"
