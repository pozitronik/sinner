# !/usr/bin/env python3
"""
Script to run the Frame Processor Server in a separate process.
"""

import logging
import signal
import sys
import time
from argparse import Namespace

from FrameProcessorServer import FrameProcessorServer
from sinner.Parameters import Parameters
from sinner.Sinner import Sinner
from sinner.utilities import suggest_max_memory, limit_resources
from sinner.validators.AttributeLoader import Rules


class Server(Sinner):
    gui: bool
    benchmark: bool
    camera: bool
    max_memory: int
    parameters: Namespace
    host: str
    port: int
    logger: logging.Logger

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'host',
                'attribute': 'host',
                'default': "127.0.0.1"
            },
            {
                'parameter': 'port',
                'attribute': 'port',
                'default': 5555
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
        """Main function to run the server."""

        # Create endpoint from host and port
        endpoint = f"tcp://{self.parameters.host}:{self.parameters.port}"
        self.logger.info(f"Starting Frame Processor Server at {endpoint}")

        # Create and start server
        server = FrameProcessorServer(self.parameters, endpoint=endpoint)

        # Set up signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            self.logger.info("Shutting down server...")
            server.stop_server()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start the server
        server.start_server()
        self.logger.info("Server started successfully")

        # Keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        finally:
            server.stop_server()
            self.logger.info("Server shut down")


if __name__ == "__main__":
    Server().run()
