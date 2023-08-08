from sinner.utilities import suggest_max_memory
from sinner.validators.AttributeLoader import AttributeLoader, Rules


class Sinner(AttributeLoader):

    # the main module cannot be documented with AttributeDocumenter, because it causes a circular import
    def rules(self) -> Rules:
        return [
            {
                'parameter': 'max-memory',
                'default': suggest_max_memory()
            },
            {
                'parameter': 'gui',
                'default': False
            },
            {
                'parameter': 'benchmark',
                'default': None,
            },
        ]