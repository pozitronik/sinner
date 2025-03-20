import threading
import time
from typing import Dict, Any, Optional, Set

import zmq

from sinner.gui.server.FrameProcessorZMQ import FrameProcessorZMQ
from sinner.models.status.StatusMixin import StatusMixin
from sinner.models.status.Mood import Mood


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

    @property
    def source_path(self) -> str | None:
        pass

    @source_path.setter
    def source_path(self, value: str | None) -> None:
        self._send_request({
            "action": "source_path",
            "source_path": value,
        })

    @property
    def target_path(self) -> str | None:
        pass

    @target_path.setter
    def target_path(self, value: str | None) -> None:
        self._send_request({
            "action": "target_path",
            "target_path": value,
        })

    @property
    def quality(self) -> int:
        pass

    @quality.setter
    def quality(self, value: int) -> None:
        self._send_request({
            "action": "quality",
            "quality": value,
        })

    def rewind(self, value: int) -> None:
        self._send_request({
            "action": "position",
            "position": value,
        })

    def await_frame(self, value: int) -> None:
        """
        Send frame request to the server and wait until it's done
        :param value:
        :return:
        """
        self._send_request_with_response({
            "action": "frame",
            "position": value,
        })

    def start(self, start_frame: int) -> None:
        self._send_request({
            "action": "start",
            "position": start_frame
        })

    def stop(self) -> None:
        self._send_request({
            "action": "stop",
        })

    def get_server_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current server status.

        Returns:
        Dict or None: Server status information or None if request failed
        """
        return self._send_request_with_response({
            "action": "status",
        })

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
                self.update_status(f"Sending request: {request}")
                self.socket.send(self._serialize_message(request))

                # Wait for response with timeout
                try:
                    response_data = self.socket.recv()
                    response = self._deserialize_message(response_data)
                    self.update_status(f"Received response: {response}")
                    return response.get("status") == "ok"
                except zmq.ZMQError as e:
                    if e.errno == zmq.EAGAIN:  # Timeout
                        self.update_status(f"Timeout waiting for response", mood=Mood.BAD)

                    else:
                        self.update_status(f"ZMQ error receiving response: {e}", mood=Mood.BAD)
                    # Reset connection and retry on error
                    # self.reset_connection()
                    return False
        except zmq.ZMQError as e:
            self.update_status(f"ZMQ error sending request: {e}, resetting", mood=Mood.BAD)
            # Reset connection and retry on error
            self.reset_connection()
            return False
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
