import threading
from typing import Callable, Any


class Event(threading.Event):
    _on_set_callback: Callable[[], Any] | None = None
    _on_clear_callback: Callable[[], Any] | None = None
    _tag: int | None = None

    def __init__(self, on_set_callback: Callable[[], Any] | None = None, on_clear_callback: Callable[[], Any] | None = None, tag: int | None = None):
        super().__init__()
        self._on_set_callback = on_set_callback
        self._on_clear_callback = on_clear_callback
        self._tag = tag

    def set_callback(self, callback: Callable[[], Any] | None = None) -> None:
        self._on_set_callback = callback

    def clear_callback(self, callback: Callable[[], Any] | None = None) -> None:
        self._on_clear_callback = callback

    def set(self, tag: int | None = None) -> None:
        super().set()
        self._tag = tag
        if self._on_set_callback:
            self._on_set_callback()

    def clear(self) -> None:
        super().clear()
        self._tag = None
        if self._on_clear_callback:
            self._on_clear_callback()

    @property
    def tag(self) -> int | None:
        return self._tag
