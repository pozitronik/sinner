from typing import Dict, Any, Optional

from sinner.gui.server.api.BaseClientAPI import BaseClientAPI


class FrameProcessorClient:
    _APIClient: BaseClientAPI

    def __init__(self, APIClient: BaseClientAPI):
        self._APIClient = APIClient
        self._APIClient.connect()

    @property
    def source_path(self) -> Optional[str]:
        return self._APIClient.send_request({"action": "source_path"})

    @source_path.setter
    def source_path(self, value: Optional[str]) -> None:
        self._APIClient.send_message({"action": "source_path", "source_path": value})

    @property
    def target_path(self) -> Optional[str]:
        return self._APIClient.send_request({"action": "target_path"})

    @target_path.setter
    def target_path(self, value: Optional[str]) -> None:
        self._APIClient.send_message({"action": "target_path", "target_path": value})

    @property
    def quality(self) -> int:
        return self._APIClient.send_request({"action": "quality"})

    @quality.setter
    def quality(self, value: int) -> None:
        self._APIClient.send_message({"action": "quality", "quality": value})

    def rewind(self, value: int) -> None:
        self._APIClient.send_message({"action": "position", "position": value})

    def await_frame(self, value: int) -> None:
        """
        Send frame request to the server and wait until it's done
        :param value:
        :return:
        """
        self._APIClient.send_message({"action": "frame", "position": value})

    def start(self, start_frame: int) -> None:
        self._APIClient.send_message({"action": "start", "position": start_frame})

    def stop(self) -> None:
        self._APIClient.send_message({"action": "stop"})

    def get_server_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current server status.

        Returns:
        Dict or None: Server status information or None if request failed
        """
        return self._APIClient.send_request({"action": "status"})

    def close(self) -> None:
        self._APIClient.disconnect()