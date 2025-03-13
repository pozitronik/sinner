#!/usr/bin/env python3
import os
import signal
import sys
from argparse import Namespace


def init_environment() -> None:
    """Инициализация переменных окружения перед импортами."""
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # do not flood with oneDNN spam

    # single thread doubles cuda performance - needs to be set before torch import
    if any(arg.startswith('--execution-provider') for arg in sys.argv):
        os.environ['OMP_NUM_THREADS'] = '1'

    if sys.version_info < (3, 10):
        print('Python version is not supported - please upgrade to 3.10 or higher.')
        sys.exit(1)


init_environment()

from sinner.Benchmark import Benchmark  # noqa: E402
from sinner.Parameters import Parameters  # noqa: E402
from sinner.BatchProcessingCore import BatchProcessingCore  # noqa: E402
from sinner.Sinner import Sinner  # noqa: E402
from sinner.gui.GUIForm import GUIForm  # noqa: E402
from sinner.webcam.WebCam import WebCam  # noqa: E402
from sinner.utilities import limit_resources  # noqa: E402


class Sin(Sinner):
    gui: bool
    benchmark: bool
    camera: bool
    max_memory: int

    parameters: Namespace

    def __init__(self) -> None:
        signal.signal(signal.SIGINT, lambda signal_number, frame: quit())
        self.parameters = Parameters().parameters
        super().__init__(parameters=self.parameters)
        self.update_parameters(self.parameters)
        limit_resources(self.max_memory)

    def run(self) -> None:
        if self.gui:
            preview = GUIForm(parameters=self.parameters)
            window = preview.show()
            window.mainloop()
        elif self.benchmark is True:
            Benchmark(parameters=self.parameters)
        elif self.camera is True:
            WebCam(parameters=self.parameters).run()
        else:
            BatchProcessingCore(parameters=self.parameters).run()


if __name__ == '__main__':
    Sin().run()
