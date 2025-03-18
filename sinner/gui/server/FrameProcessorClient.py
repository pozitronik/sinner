import threading
import time
from typing import Dict, Any, Optional, Set

import zmq

from sinner.models.status.StatusMixin import StatusMixin
from sinner.models.status.Mood import Mood

from FrameProcessorZMQ import FrameProcessorZMQ


class FrameProcessorClient(FrameProcessorZMQ, StatusMixin):
    def __init__(self, endpoint: str = "tcp://127.0.0.1:5555", timeout: int = 1000):
        """
        Initialize the frame processor client.

        Parameters:
        endpoint (str): ZeroMQ endpoint for communication
        timeout (int): Socket timeout in milliseconds
        """
        super().__init__(endpoint)
        self.timeout = timeout
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, timeout)
        self.socket.connect(self.endpoint)
        self._lock = threading.Lock()
        self._processed_frames: Set[int] = set()
        self._last_update_time = 0
        self._update_interval = 1.0  # Seconds between cached frame list updates

        self.update_status(f"Frame processor client connected to {self.endpoint}")

    """Client component for interacting with the frame processor server."""

    def request_frame_processing(self, frame_index: int) -> bool:
        """
        Request processing of a specific frame.

        Parameters:
        frame_index (int): Frame index to process

        Returns:
        bool: True if request was successful, False otherwise
        """
        if frame_index in self._processed_frames:
            return True

        request = self.build_process_request(frame_index)
        return self._send_request(request)

    def update_requested_index(self, index: int) -> bool:
        """
        Update the server with the latest requested frame index.
        This helps the server prioritize processing.

        Parameters:
        index (int): Current requested frame index

        Returns:
        bool: True if update was successful, False otherwise
        """
        request = {"action": "update_requested_index", "index": index}
        return self._send_request(request)

    def set_source_target(self, source_path: str, target_path: str) -> bool:
        """
        Set source and target paths on the server.

        Parameters:
        source_path (str): Path to source file/directory
        target_path (str): Path to target file/directory

        Returns:
        bool: True if setting was successful, False otherwise
        """
        request = {
            "action": "set_source_target",
            "source_path": source_path,
            "target_path": target_path
        }
        return self._send_request(request)

    def get_server_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current server status.

        Returns:
        Dict or None: Server status information or None if request failed
        """
        request = self.build_status_request()
        response = self._send_request_with_response(request)
        return response

    def get_processed_frames(self, force_update: bool = False) -> Set[int]:
        """
        Get the set of processed frame indices.
        Uses caching to avoid excessive requests.

        Parameters:
        force_update (bool): Force update of the cache

        Returns:
        Set[int]: Set of processed frame indices
        """
        current_time = time.time()

        # Update cache if needed
        if force_update or (current_time - self._last_update_time) > self._update_interval:
            request = self.build_list_processed_request()
            response = self._send_request_with_response(request)

            if response and "processed_frames" in response:
                with self._lock:
                    self._processed_frames = set(response["processed_frames"])
                self._last_update_time = current_time

        return self._processed_frames.copy()

    def is_frame_processed(self, frame_index: int) -> bool:
        """
        Check if a specific frame has been processed.

        Parameters:
        frame_index (int): Frame index to check

        Returns:
        bool: True if frame is processed, False otherwise
        """
        return frame_index in self.get_processed_frames()

    def _send_request(self, request: Dict[str, Any]) -> bool:
        """
        Send a request to the server and return success status.

        Parameters:
        request (Dict): Request to send

        Returns:
        bool: True if request was successful, False otherwise
        """
        try:
            with self._lock:
                self.update_status(f"Request: {request}")
                self.socket.send(self._serialize_message(request))
                response_data = self.socket.recv()
                response = self._deserialize_message(response_data)
                self.update_status(f"Response: {response}")
                return response.get("status") == "ok"
        except zmq.ZMQError as e:
            self.update_status(f"ZeroMQ error: {e}, resetting", mood=Mood.BAD)
            # Автоматически сбрасываем соединение при ошибке
            self.reset_connection()
            return self._send_request(request)
        except Exception as e:
            self.update_status(f"Error sending request: {e}", mood=Mood.BAD)
            self.logger.exception("Client request error")
            return False

    def _send_request_with_response(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a request to the server and return full response.

        Parameters:
        request (Dict): Request to send

        Returns:
        Dict or None: Server response or None if failed
        """
        try:
            with self._lock:
                self.socket.send(self._serialize_message(request))
                response_data = self.socket.recv()
                response = self._deserialize_message(response_data)

                if response.get("status") != "ok":
                    error_msg = response.get("message", "Unknown error")
                    self.update_status(f"Server returned error: {error_msg}", mood=Mood.BAD)
                    return None

                return response
        except zmq.ZMQError as e:
            self.update_status(f"ZeroMQ error: {e}", mood=Mood.BAD)
            return None
        except Exception as e:
            self.update_status(f"Error sending request: {e}", mood=Mood.BAD)
            self.logger.exception("Client request error")
            return None

    def reset_connection(self) -> bool:
        """
        Reset the connection to the server. Useful for error recovery.

        Returns:
        bool: True if connection was reset successfully
        """
        try:
            with self._lock:
                self.socket.close()
                self.socket = self.context.socket(zmq.REQ)
                self.socket.setsockopt(zmq.RCVTIMEO, self.timeout)
                self.socket.connect(self.endpoint)
                self.update_status("Connection to server reset")
                return True
        except Exception as e:
            self.update_status(f"Error resetting connection: {e}", mood=Mood.BAD)
            return False
