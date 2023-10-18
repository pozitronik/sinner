from pyvirtualcam import Camera

from sinner.typing import Frame


class NoDevice(Camera):
    def send(self, frame: Frame) -> None:
        return None

    def sleep_until_next_frame(self) -> None:
        return None
