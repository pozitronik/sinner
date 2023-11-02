import threading
from typing import Callable, Any


class Event(threading.Event):
    _on_set_callback: Callable[[Any], Any] | None = None
    _on_clear_callback: Callable[[Any], Any] | None = None

    def __init__(self, on_set_callback: Callable[[Any], Any] | None = None, on_clear_callback: Callable[[Any], Any] | None = None):
        super().__init__()
        self._on_set_callback = on_set_callback
        self._on_clear_callback = on_clear_callback

    def set_callback(self, callback: Callable[[Any], Any] | None = None) -> None:
        self._on_set_callback = callback

    def clear_callback(self, callback: Callable[[Any], Any] | None = None) -> None:
        self._on_clear_callback = callback

    def set(self) -> None:
        super().set()
        if self._on_set_callback:
            self._on_set_callback()

    def clear(self) -> None:
        super().clear()
        if self._on_clear_callback:
            self._on_clear_callback()
