from typing import Optional

from sinner.gui.server.api.BaseClientAPI import BaseClientAPI
from sinner.gui.server.api.messages.RequestMessage import RequestMessage
from sinner.gui.server.api.messages.ResponseMessage import ResponseMessage
from sinner.models.MediaMetaData import MediaMetaData


class FrameProcessingClient:
    _APIClient: BaseClientAPI

    def __init__(self, APIClient: BaseClientAPI):
        self._APIClient = APIClient
        self._APIClient.connect()

    @property
    def source_path(self) -> Optional[str]:
        response: ResponseMessage = self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_SOURCE))
        if response.is_ok():
            return response.source_path
        else:
            return None

    @source_path.setter
    def source_path(self, value: Optional[str]) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.SET_SOURCE, source_path=value))

    @property
    def target_path(self) -> Optional[str]:
        response: ResponseMessage = self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_TARGET))
        if response.is_ok():
            return response.target_path
        else:
            return None

    @target_path.setter
    def target_path(self, value: Optional[str]) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.SET_TARGET, target_path=value))

    @property
    def quality(self) -> int:
        response: ResponseMessage = self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_QUALITY))
        if response.is_ok():
            return response.quality
        else:
            return 100

    @quality.setter
    def quality(self, value: int) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.SET_QUALITY, quality=value))

    def rewind(self, value: int) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.SET_POSITION, position=value))

    def await_frame(self, value: int) -> bool:
        """
        Send frame request to the server and wait until it's done
        :param value:
        :return: bool Frame ready status
        """
        return self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_FRAME, position=value)).is_ok()

    def start(self, start_frame: int) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.START_PROCESSING, position=start_frame))

    def stop(self) -> None:
        self._APIClient.send_request(RequestMessage.create(RequestMessage.STOP_PROCESSING))

    @property
    def server_status(self) -> bool:
        """
        Get current server status.

        Returns:
        Dict or None: Server status information or None if request failed todo
        """
        return self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_STATUS)).is_ok()

    @property
    def metadata(self) -> MediaMetaData:
        response: ResponseMessage = self._APIClient.send_request(RequestMessage.create(RequestMessage.REQ_METADATA))
        if response.is_ok():
            return MediaMetaData(resolution=response.resolution, fps=response.fps, frames_count=response.frames_count)
        else:
            return MediaMetaData()

    def close(self) -> None:
        self._APIClient.disconnect()
