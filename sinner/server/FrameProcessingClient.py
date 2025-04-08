from typing import Optional

from sinner.server.api.BaseClientAPI import BaseClientAPI
from sinner.server.api.messages.RequestMessage import RequestMessage
from sinner.server.api.messages.ResponseMessage import ResponseMessage
from sinner.helpers.FrameHelper import from_b64
from sinner.models.MediaMetaData import MediaMetaData
from sinner.models.NumberedFrame import NumberedFrame


class FrameProcessingClient:
    _APIClient: BaseClientAPI

    def __init__(self, APIClient: BaseClientAPI):
        self._APIClient = APIClient
        self._APIClient.connect()

    @property
    def connected(self) -> bool:
        return self._APIClient.connected

    @property
    def source_path(self) -> Optional[str]:
        response: ResponseMessage = self._APIClient.send_request(RequestMessage(RequestMessage.GET_SOURCE))
        if response.is_ok():
            return response.source_path
        else:
            return None

    @source_path.setter
    def source_path(self, value: Optional[str]) -> None:
        self._APIClient.send_request(RequestMessage(RequestMessage.SET_SOURCE, source_path=value))

    @property
    def target_path(self) -> Optional[str]:
        response: ResponseMessage = self._APIClient.send_request(RequestMessage(RequestMessage.GET_TARGET))
        if response.is_ok():
            return response.target_path
        else:
            return None

    @target_path.setter
    def target_path(self, value: Optional[str]) -> None:
        self._APIClient.send_request(RequestMessage(RequestMessage.SET_TARGET, target_path=value))

    @property
    def quality(self) -> int:
        response: ResponseMessage = self._APIClient.send_request(RequestMessage(RequestMessage.GET_QUALITY))
        if response.is_ok():
            return response.quality
        else:
            return 100

    @quality.setter
    def quality(self, value: int) -> None:
        self._APIClient.send_request(RequestMessage(RequestMessage.SET_QUALITY, quality=value))

    def rewind(self, value: int) -> None:
        self._APIClient.send_request(RequestMessage(RequestMessage.SET_POSITION, position=value))

    def get_processed_frame(self, value: int) -> bool:
        """
        Send frame generation request to the server and wait until it's done.
        :param value:
        :return: bool Frame ready status
        """
        return self._APIClient.send_request(RequestMessage(RequestMessage.CMD_FRAME_PROCESSED, position=value)).is_ok()

    def get_frame(self, value: int) -> Optional[NumberedFrame]:
        """
        Send initial frame request to the server and wait until it's done
        Assumed it is some kind of fallback mode
        :param value:
        :return: Optional[NumberedFrame] The requested unprocessed frame
        """
        response = self._APIClient.send_request(RequestMessage(RequestMessage.GET_FRAME, position=value))
        if response.is_ok():
            frame = from_b64(response.frame, shape=response.shape)
            return NumberedFrame(index=value, frame=frame)
        else:
            return None

    def start(self, start_frame: int) -> None:
        self._APIClient.send_request(RequestMessage(RequestMessage.CMD_START_PROCESSING, position=start_frame))

    def stop(self) -> None:
        self._APIClient.send_request(RequestMessage(RequestMessage.CMD_STOP_PROCESSING))

    @property
    def server_status(self) -> bool:
        """
        Get current server status.

        Returns:
        Dict or None: Server status information or None if request failed todo
        """
        return self._APIClient.send_request(RequestMessage(RequestMessage.GET_STATUS)).is_ok()

    @property
    def metadata(self) -> MediaMetaData:
        response: ResponseMessage = self._APIClient.send_request(RequestMessage(RequestMessage.GET_METADATA))
        if response.is_ok():
            return MediaMetaData(resolution=response.resolution, fps=response.fps, frames_count=response.frames_count, render_resolution=response.render_resolution)
        else:
            return MediaMetaData()

    def close(self) -> None:
        self._APIClient.disconnect()
