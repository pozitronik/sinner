from typing import List, Any

from sinner.gui.controls.ProgressIndicator.BaseProgressIndicator import BaseProgressIndicator


#  stub to disable progress indicator, when needed
class DummyProgressIndicator(BaseProgressIndicator):
    def __init__(self, **kwargs):  # type: ignore[no-untyped-def]
        pass

    def set_segments(self, segments: int) -> None:
        pass

    def update_states(self, states: List[int]) -> None:
        pass

    def set_segment_value(self, index: int, value: int) -> None:
        pass

    def set_segment_values(self, indexes: List[int], value: int, reset: bool = True, update: bool = True) -> None:
        pass

    async def set_segment_value_async(self, index: int, value: int) -> None:
        pass

    def place_configure(self, cnf={}, **kw) -> None:  # type: ignore[no-untyped-def]
        pass

    @property
    def pass_through(self) -> Any:
        return None

    @pass_through.setter
    def pass_through(self, value: Any) -> None:
        pass
