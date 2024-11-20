#!/usr/bin/env python3
import os
import signal
import sys
from argparse import Namespace

if sys.version_info < (3, 10):
    print('Python version is not supported - please upgrade to 3.10 or higher.')
    quit()

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # disable annoying message
os.environ['OMP_NUM_THREADS'] = '1'  # single thread doubles cuda performance - needs to be set before torch import

from sinner.Benchmark import Benchmark
from sinner.Parameters import Parameters
from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.Sinner import Sinner
from sinner.gui.GUIForm import GUIForm
from sinner.webcam.WebCam import WebCam
from sinner.utilities import limit_resources


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
