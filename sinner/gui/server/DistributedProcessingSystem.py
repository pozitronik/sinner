import os
import subprocess
import sys
import time
from argparse import Namespace
from typing import Optional

from sinner.models.status.StatusMixin import StatusMixin
from sinner.models.status.Mood import Mood
from sinner.validators.AttributeLoader import Rules, AttributeLoader

from FrameProcessorClient import FrameProcessorClient
from FrameProcessorServer import FrameProcessorServer


class DistributedProcessingSystem(AttributeLoader, StatusMixin):
    """
    Main coordinator for the distributed processing system.
    This class can start server as a separate process and initialize client connections.
    """

    # Configuration
    zmq_endpoint: str
    server_mode: str
    server_python_executable: str
    server_script_path: str

    # Components
    _server: Optional[FrameProcessorServer] = None
    _client: Optional[FrameProcessorClient] = None
    _server_process: Optional[subprocess.Popen] = None

    def rules(self) -> Rules:
        return [
            {
                'parameter': 'zmq-endpoint',
                'attribute': 'zmq_endpoint',
                'default': "tcp://127.0.0.1:5555",
                'help': 'ZeroMQ endpoint for the frame processor server'
            },
            {
                'parameter': 'server-mode',
                'attribute': 'server_mode',
                'default': "integrated",  # integrated, subprocess, or external
                'choices': ["integrated", "subprocess", "external"],
                'help': 'Mode for running the processor server'
            },
            {
                'parameter': {'server-python', 'python-executable'},
                'attribute': 'server_python_executable',
                'default': sys.executable,
                'help': 'Python executable for launching server subprocess'
            },
            {
                'parameter': {'server-script', 'server-path'},
                'attribute': 'server_script_path',
                'default': os.path.join(os.path.dirname(__file__), "run_server.py"),
                'help': 'Path to the server script for subprocess mode'
            },
            {
                'module_help': 'Distributed processing system coordinator'
            }
        ]

    def __init__(self, parameters: Namespace):
        """
        Initialize the distributed processing system.

        Parameters:
        parameters (Namespace): Application parameters
        """
        super().__init__(parameters)
        self.parameters = parameters

        # Parse host and port from endpoint
        self._parse_endpoint()

        # Initialize system based on mode
        self._initialize_system()

    def _parse_endpoint(self) -> None:
        """Parse host and port from the ZMQ endpoint."""
        # Assuming format like tcp://127.0.0.1:5555
        try:
            parts = self.zmq_endpoint.split(":")
            self.host = parts[1].replace("//", "")
            self.port = int(parts[2])
        except (IndexError, ValueError):
            self.host = "127.0.0.1"
            self.port = 5555
            self.update_status(f"Invalid endpoint format: {self.zmq_endpoint}, using {self.host}:{self.port}",
                               mood=Mood.BAD)

    def _initialize_system(self) -> None:
        """Initialize the processing system based on server mode."""
        if self.server_mode == "integrated":
            self._initialize_integrated_mode()
        elif self.server_mode == "subprocess":
            self._initialize_subprocess_mode()
        elif self.server_mode == "external":
            self._initialize_external_mode()
        else:
            self.update_status(f"Unknown server mode: {self.server_mode}, falling back to external mode", mood=Mood.BAD)
            self._initialize_external_mode()

    def _initialize_integrated_mode(self) -> None:
        """Initialize server and client in the same process."""
        self.update_status("Initializing integrated mode")

        # Create server
        self._server = FrameProcessorServer(self.parameters, endpoint=self.zmq_endpoint)
        self._server.start_server()

        # Create client
        self._client = FrameProcessorClient(endpoint=self.zmq_endpoint)

        # Wait for server to be ready
        time.sleep(0.5)

    def _initialize_subprocess_mode(self) -> None:
        """Initialize server in a subprocess and client in this process."""
        self.update_status("Initializing subprocess mode")

        # Validate server script path
        if not os.path.exists(self.server_script_path):
            self.update_status(f"Server script not found at {self.server_script_path}", mood=Mood.BAD)
            self._initialize_external_mode()
            return

        # Start server process
        try:
            server_command = [
                self.server_python_executable,
                self.server_script_path,
                "--host", self.host,
                "--port", str(self.port)
            ]

            # Add parameters from current namespace
            for key, value in vars(self.parameters).items():
                if key not in ["host", "port"] and value is not None:
                    if isinstance(value, bool):
                        if value:
                            server_command.append(f"--{key}")
                    else:
                        server_command.append(f"--{key}")
                        server_command.append(str(value))

            self._server_process = subprocess.Popen(
                server_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.update_status(f"Server subprocess started with PID {self._server_process.pid}")

            # Create client
            self._client = FrameProcessorClient(endpoint=self.zmq_endpoint)

            # Wait for server to be ready
            time.sleep(1.0)

        except Exception as e:
            self.update_status(f"Failed to start server subprocess: {e}", mood=Mood.BAD)
            self._initialize_external_mode()

    def _initialize_external_mode(self) -> None:
        """Initialize client only, assuming server is running externally."""
        self.update_status("Initializing external mode - connecting to existing server")

        # Create client only
        self._client = FrameProcessorClient(endpoint=self.zmq_endpoint)

        # Test connection
        try:
            status = self._client.get_server_status()
            if status:
                self.update_status("Connected to external server successfully")
            else:
                self.update_status("Failed to connect to external server", mood=Mood.BAD)
        except Exception as e:
            self.update_status(f"Error connecting to external server: {e}", mood=Mood.BAD)

    def get_client(self) -> Optional[FrameProcessorClient]:
        """Get the frame processor client."""
        return self._client

    def get_server(self) -> Optional[FrameProcessorServer]:
        """Get the frame processor server (only available in integrated mode)."""
        return self._server

    def shutdown(self) -> None:
        """Shutdown the distributed processing system."""
        self.update_status("Shutting down distributed processing system")

        # Stop server if in integrated mode
        if self._server:
            self._server.stop_server()

        # Close client connection
        if self._client:
            self._client.close()

        # Terminate subprocess if running
        if self._server_process:
            try:
                self._server_process.terminate()
                self._server_process.wait(timeout=3)
                self.update_status("Server subprocess terminated")
            except subprocess.TimeoutExpired:
                self._server_process.kill()
                self.update_status("Server subprocess killed", mood=Mood.BAD)
            except Exception as e:
                self.update_status(f"Error terminating server subprocess: {e}", mood=Mood.BAD)
