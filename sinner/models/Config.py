from argparse import Namespace
from configparser import ConfigParser
from typing import Any

from sinner.utilities import get_app_dir


class Config:
    _filename: str
    _config: ConfigParser

    def __init__(self, parameters: Namespace):
        self._filename = parameters.ini if hasattr(parameters, 'ini') else get_app_dir('sinner.ini')
        self._config = ConfigParser()

    def read_section(self, section: str) -> Namespace | None:
        module_parameters: Namespace = Namespace()
        self._config.read(self._filename)
        if self._config.has_section(section):
            for key in self._config[section]:
                value = self._config[section][key]
                key = key.replace('-', '_')
                module_parameters.__setattr__(key, value)
            return module_parameters
        return None

    def set_key(self, section: str, key: str, value: Any | None) -> None:
        self._config.read(self._filename)
        if value:
            self._config.set(section, key, str(value))
        else:
            self._config.remove_option(section, key)
        with open(self._filename, 'w') as config_file:
            self._config.write(config_file)
