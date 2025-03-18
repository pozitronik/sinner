import threading
from argparse import Namespace
from typing import Dict, Any, List, Set, Optional, Tuple

import zmq

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.gui.server.FrameProcessorZMQ import FrameProcessorZMQ
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.NoneHandler import NoneHandler
from sinner.models.FrameDirectoryBuffer import FrameDirectoryBuffer
from sinner.models.FrameTimeLine import FrameTimeLine
from sinner.models.MovingAverage import MovingAverage
from sinner.models.status.StatusMixin import StatusMixin
from sinner.models.status.Mood import Mood
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.utilities import suggest_execution_threads, suggest_temp_dir
from sinner.validators.AttributeLoader import Rules, AttributeLoader


class FrameProcessorServer(FrameProcessorZMQ, AttributeLoader, StatusMixin):
    """Server component for processing frames in a separate process."""

    # configuration variables
    frame_processor: List[str]
    temp_dir: str
    execution_threads: int
    bootstrap_processors: bool
    _scale_quality: float
    host: str
    port: int

    # internal objects
    TimeLine: FrameTimeLine
    _processors: Dict[str, BaseFrameProcessor]
    _target_handler: Optional[BaseFrameHandler] = None
    _buffer: Optional[FrameDirectoryBuffer] = None

    # processing state
    _processing: Set[int] = set()  # frames currently in processing
    _processed: Set[int] = set()  # frames that have been processed
    _source_path: Optional[str] = None
    _target_path: Optional[str] = None

    # metrics
    _average_processing_time: MovingAverage = MovingAverage(window_size=10)
    _average_frame_skip: MovingAverage = MovingAverage(window_size=10)
    _processing_fps: float = 1.0
    _processing_delta: int = 0
    _last_requested_index: int = 0
    _last_added_index: int = 0

    # threading
    _running: bool = False
    _server_thread: Optional[threading.Thread] = None

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'frame-processor', 'processor', 'processors'},
                'attribute': 'frame_processor',
                'default': ['FaceSwapper'],
                'required': True,
                'help': 'The set of frame processors to handle the target'
            },
            {
                'parameter': 'execution-threads',
                'default': suggest_execution_threads(),
                'help': 'The count of simultaneous processing threads'
            },
            {
                'parameter': {'source', 'source-path'},
                'attribute': '_source_path'
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': '_target_path'
            },
            {
                'parameter': {'quality', 'scale-quality'},
                'attribute': '_scale_quality',
                'default': 1,
                'help': 'Processing scale quality'
            },
            {
                'parameter': ['bootstrap_processors', 'bootstrap'],
                'attribute': 'bootstrap_processors',
                'default': True,
                'help': 'Bootstrap frame processors on startup'
            },
            {
                'parameter': 'temp-dir',
                'default': lambda: suggest_temp_dir(self.temp_dir),
                'help': 'Select the directory for temporary files'
            },
            {
                'parameter': 'host',
                'attribute': 'host',
                'default': "127.0.0.1",
                'help': 'Host for ZeroMQ binding'
            },
            {
                'parameter': 'port',
                'attribute': 'port',
                'default': 5555,
                'help': 'Port for ZeroMQ binding'
            },
            {
                'module_help': 'The server for frame processing'
            }
        ]

    def __init__(self, parameters: Namespace, endpoint: Optional[str] = None):
        """
        Initialize the frame processor server.

        Parameters:
        parameters (Namespace): Application parameters
        endpoint (str, optional): ZeroMQ endpoint override for communication
        """
        # Initialize attribute loader first
        AttributeLoader.__init__(self, parameters)

        # Use explicit endpoint if provided, otherwise construct from host/port
        if endpoint is None:
            endpoint = f"tcp://{self.host}:{self.port}"

        # Initialize ZMQ
        FrameProcessorZMQ.__init__(self, endpoint)

        self.parameters = parameters
        self._processors = {}

        # Initialize processors if bootstrap is enabled
        if self.bootstrap_processors:
            self._processors = self.processors

        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self.endpoint)

        self.update_status(f"Frame processor server initialized at {self.endpoint}")

    @property
    def processors(self) -> Dict[str, BaseFrameProcessor]:
        """Get or initialize frame processors."""
        try:
            for processor_name in self.frame_processor:
                if processor_name not in self._processors:
                    self._processors[processor_name] = BaseFrameProcessor.create(processor_name, self.parameters)
        except Exception as exception:  # skip, if parameters is not enough for processor
            self.update_status(message=str(exception), mood=Mood.BAD)
            pass
        return self._processors

    @property
    def frame_handler(self) -> BaseFrameHandler:
        if self._target_handler is None:
            if self._target_path is None:
                self._target_handler = NoneHandler('', self.parameters)
            else:
                self._target_handler = BatchProcessingCore.suggest_handler(self._target_path, self.parameters)
        return self._target_handler

    def start_server(self) -> None:
        """Start the server in a separate thread."""
        if self._server_thread is not None and self._server_thread.is_alive():
            self.update_status("Server is already running")
            return

        self._running = True
        self._server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self._server_thread.start()
        self.update_status("Frame processor server started")

    def stop_server(self) -> None:
        """Stop the server thread."""
        self._running = False
        if self._server_thread:
            self._server_thread.join(timeout=2.0)
            if self._server_thread.is_alive():
                self.update_status("Server thread did not terminate gracefully", mood=Mood.BAD)
            else:
                self.update_status("Server stopped")
        self.close()

    def _server_loop(self) -> None:
        """Main server loop to process requests."""
        self.update_status("Server loop started")

        while self._running:
            try:
                # Use poll to check for messages with timeout
                # if self.socket.poll(100) == 0:  # 100ms timeout
                #     # Check completed futures
                #     self._check_completed_futures(futures)
                #     continue

                # Process incoming message
                message_data = self.socket.recv()
                message = self._deserialize_message(message_data)

                self.logger.info(f"Received message: {message}")
                response = self._handle_request(message)

                # Send response
                self.socket.send(self._serialize_message(response))

                # Check completed futures
                # self._check_completed_futures(futures)

            except zmq.ZMQError as e:
                self.update_status(f"ZMQ error: {e}", mood=Mood.BAD)
            except Exception as e:
                self.update_status(f"Error in server loop: {e}", mood=Mood.BAD)
                self.logger.exception("Server error")

        self.update_status("Server loop ended")

    def _handle_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle client request and return response."""
        action = message.get("action", "")

        if action == "source_path":
            self.source_path = message.get("source_path")
            return self.build_response("ok", message="Source path set")

        if action == "target_path":
            self.target_path = message.get("target_path")
            return self.build_response("ok", message="Target path set")

        else:
            return self.build_response("error", message=f"Unknown action: {action}")

    def reload_parameters(self) -> None:
        self._target_handler = None
        super().__init__(self.parameters)
        for _, processor in self.processors.items():
            processor.load(self.parameters)

    @property
    def source_path(self) -> str | None:
        return self._source_path

    @source_path.setter
    def source_path(self, value: str | None) -> None:
        self.parameters.source = value
        self.reload_parameters()
        self.TimeLine = FrameTimeLine(source_name=self._source_path, target_name=self._target_path, temp_dir=self.temp_dir, frame_time=self.frame_handler.frame_time, start_frame=self.TimeLine.last_requested_index, end_frame=self.frame_handler.fc)

    @property
    def target_path(self) -> str | None:
        return self._target_path

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        self.parameters.target = value
        self.reload_parameters()
        self.TimeLine = FrameTimeLine(source_name=self._source_path, target_name=self._target_path, temp_dir=self.temp_dir, frame_time=self.frame_handler.frame_time, start_frame=1, end_frame=self.frame_handler.fc)
