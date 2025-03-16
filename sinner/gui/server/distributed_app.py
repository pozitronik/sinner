#!/usr/bin/env python3
"""
Main entry point for running the application in distributed mode.
"""

import logging
import signal
import sys
from argparse import Namespace

from DistributedGUIForm import create_distributed_gui_form
from sinner.Parameters import Parameters
from sinner.Sinner import Sinner
from sinner.utilities import suggest_max_memory, limit_resources
from sinner.validators.AttributeLoader import Rules


class Client(Sinner):
    gui: bool
    benchmark: bool
    camera: bool
    max_memory: int
    parameters: Namespace
    zmq_endpoint: str
    server_mode: list[str]
    logger: logging.Logger

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'zmq-endpoint',
                'attribute': 'zmq_endpoint',
                'default': "tcp://127.0.0.1:5555"
            },
            {
                'parameter': 'server-mode',
                'attribute': 'server_mode',
                'choices': ["integrated", "subprocess", "external"],
                'default': "integrated"
            },
            {
                'parameter': 'max-memory',
                'attribute': 'max_memory',
                'default': suggest_max_memory(),
                'help': 'The maximum amount of RAM (in GB) that will be allowed for use'
            },
            {
                'module_help': 'The main application'
            }
        ]

    def __init__(self) -> None:
        signal.signal(signal.SIGINT, lambda signal_number, frame: quit())
        self.parameters = Parameters().parameters
        super().__init__(parameters=self.parameters)
        self.update_parameters(self.parameters)
        self.setup_logging()
        limit_resources(self.max_memory)

    def setup_logging(self):
        """Set up basic logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('frame_processor_server')

    def run(self):
        self.logger.info(f"Starting distributed application with endpoint {self.parameters.zmq_endpoint}")

        # Create and run the distributed GUI form
        gui_form = create_distributed_gui_form(self.parameters)
        window = gui_form.show()

        # Start the main loop
        self.logger.info("Starting main application loop")
        window.mainloop()


if __name__ == "__main__":
    Client().run()
