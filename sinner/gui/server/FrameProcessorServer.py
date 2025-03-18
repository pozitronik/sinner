import threading
from argparse import Namespace
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Dict, Any, List, Set, Optional, Tuple

import zmq

from sinner.BatchProcessingCore import BatchProcessingCore
from sinner.gui.server.FrameProcessorZMQ import FrameProcessorZMQ
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.handlers.frame.NoneHandler import NoneHandler
from sinner.models.FrameDirectoryBuffer import FrameDirectoryBuffer
from sinner.models.MovingAverage import MovingAverage
from sinner.models.PerfCounter import PerfCounter
from sinner.models.status.StatusMixin import StatusMixin
from sinner.models.status.Mood import Mood
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.helpers.FrameHelper import scale
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

        with ProcessPoolExecutor(max_workers=self.execution_threads) as executor:
            futures: List[Future] = []

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
                    response = self._handle_request(message, executor, futures)

                    # Send response
                    self.socket.send(self._serialize_message(response))

                    # Check completed futures
                    self._check_completed_futures(futures)

                except zmq.ZMQError as e:
                    self.update_status(f"ZMQ error: {e}", mood=Mood.BAD)
                except Exception as e:
                    self.update_status(f"Error in server loop: {e}", mood=Mood.BAD)
                    self.logger.exception("Server error")

        self.update_status("Server loop ended")

    def _handle_request(self, message: Dict[str, Any], executor: ProcessPoolExecutor, futures: List[Future]) -> Dict[str, Any]:
        """Handle client request and return response."""
        action = message.get("action", "")

        if action == "process":
            frame_index = message.get("frame_index")
            if frame_index is None:
                return self.build_response("error", message="Missing frame_index")

            if frame_index in self._processing or frame_index in self._processed:
                return self.build_response("ok", message=f"Frame {frame_index} already in processing or processed")

            self._submit_frame_processing(frame_index, executor, futures)
            return self.build_response("ok", message=f"Processing frame {frame_index}")

        elif action == "status":
            return self.build_response("ok", processing_count=len(self._processing), processed_count=len(self._processed), processing_fps=self._processing_fps)

        elif action == "list_processed":
            return self.build_response("ok", processed_frames=sorted(list(self._processed)))

        elif action == "set_handler":
            # This would be a more complex operation requiring passing handler information
            # For simplicity, we're not implementing full serialization of handlers here
            return self.build_response("error", message="Handler setting not supported in basic mode")

        elif action == "set_source_target":
            self._source_path = message.get("source_path")
            self._target_path = message.get("target_path")
            return self.build_response("ok", message="Source and target paths set")

        elif action == "update_requested_index":
            self._last_requested_index = message.get("index", self._last_requested_index)
            return self.build_response("ok", last_requested_index=self._last_requested_index)

        else:
            return self.build_response("error", message=f"Unknown action: {action}")

    def _submit_frame_processing(self, frame_index: int, executor: ProcessPoolExecutor, futures: List[Future]) -> None:
        """Submit a frame for processing to the process pool."""
        if self.frame_handler is None:
            self.update_status("Cannot process frame: frame handler not set", mood=Mood.BAD)
            return

        self._processing.add(frame_index)
        future = executor.submit(self._process_frame_worker, frame_index)
        futures.append(future)

        # Update processing metrics
        self._update_processing_metrics()

    def _check_completed_futures(self, futures: List[Future]) -> None:
        """Check and handle completed futures."""
        completed_futures = [f for f in futures if f.done()]

        for future in completed_futures:
            try:
                result = future.result()
                if result:
                    process_time, frame_index = result
                    self._average_processing_time.update(process_time / self.execution_threads)

                    # Update states
                    if frame_index in self._processing:
                        self._processing.remove(frame_index)
                    self._processed.add(frame_index)

                    # Update metrics
                    self._processing_fps = 1 / self._average_processing_time.get_average()
                    self._last_added_index = max(self._last_added_index, frame_index)

                    self.update_status(f"Processed frame {frame_index}, {self._processing_fps:.2f} FPS")
            except Exception as e:
                self.update_status(f"Error processing frame: {e}", mood=Mood.BAD)

            futures.remove(future)

    def _process_frame_worker(self, frame_index: int) -> Optional[Tuple[float, int]]:
        """
        Worker function for processing a single frame.
        This is designed to be called in a ProcessPoolExecutor.

        Returns:
            Tuple containing (process_time, frame_index) or None if failed
        """
        if self.frame_handler is None or self._buffer is None:
            return None

        try:
            # Extract frame from the handler
            n_frame = self.frame_handler.extract_frame(frame_index)

            # Scale the frame if needed
            n_frame.frame = scale(n_frame.frame, self._scale_quality)

            # Process the frame
            with PerfCounter() as frame_render_time:
                for processor in self.processors.values():
                    n_frame.frame = processor.process_frame(n_frame.frame)

            # Save the processed frame
            self._buffer.add_frame(n_frame)

            return frame_render_time.execution_time, n_frame.index

        except Exception as e:
            self.logger.error(f"Error processing frame {frame_index}: {e}")
            return None

    def _update_processing_metrics(self) -> None:
        """Update processing metrics based on current state."""
        if self._processing_fps > 0:
            self._average_frame_skip.update(self.frame_handler.fps / self._processing_fps if self.frame_handler else 1.0)

        # Adjust processing delta based on current state
        if (self._last_added_index > self._last_requested_index and
                self._processing_delta > self._average_frame_skip.get_average()):
            self._processing_delta -= 1
        elif self._last_added_index < self._last_requested_index:
            self._processing_delta += 1
