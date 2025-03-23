from typing import Dict, Any, Optional

from sinner.gui.server.api.BaseClientAPI import BaseClientAPI
from sinner.gui.server.api.RequestMessage import RequestMessage


class FrameProcessorClient:
    _APIClient: BaseClientAPI

    def __init__(self, APIClient: BaseClientAPI):
        self._APIClient = APIClient
        self._APIClient.connect()

    @property
    def source_path(self) -> Optional[str]:
        return self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_SOURCE))

    @source_path.setter
    def source_path(self, value: Optional[str]) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.SET_SOURCE, source_path=value))

    @property
    def target_path(self) -> Optional[str]:
        return self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_TARGET))

    @target_path.setter
    def target_path(self, value: Optional[str]) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.SET_TARGET, target_path=value))

    @property
    def quality(self) -> int:
        return self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_QUALITY))

    @quality.setter
    def quality(self, value: int) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.SET_QUALITY, quality=value))

    def rewind(self, value: int) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.SET_POSITION, position=value))

    def await_frame(self, value: int) -> None:
        """
        Send frame request to the server and wait until it's done
        :param value:
        :return:
        """
        self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_FRAME, position=value))

    def start(self, start_frame: int) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.START_PROCESSING, position=start_frame))

    def stop(self) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.STOP_PROCESSING))

    def get_server_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current server status.

        Returns:
        Dict or None: Server status information or None if request failed
        """
        return self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_STATUS))

    def close(self) -> None:
        self._APIClient.disconnect()
