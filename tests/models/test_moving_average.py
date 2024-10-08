import pytest
from collections import deque
from typing import List

from sinner.models.MovingAverage import MovingAverage


@pytest.fixture
def ma_with_window():
    return MovingAverage(window_size=3)


@pytest.fixture
def ma_without_window():
    return MovingAverage()


def test_init_with_window():
    ma = MovingAverage(window_size=5)
    assert ma.window_size == 5
    assert isinstance(ma.window, deque)
    assert ma.window.maxlen == 5


def test_init_without_window():
    ma = MovingAverage()
    assert ma.window_size == 0
    assert ma.sum == 0
    assert ma.count == 0


def test_update_with_window(ma_with_window):
    ma_with_window.update(1)
    ma_with_window.update(2)
    ma_with_window.update(3)
    ma_with_window.update(4)
    assert list(ma_with_window.window) == [2, 3, 4]


def test_update_without_window(ma_without_window):
    ma_without_window.update(1)
    ma_without_window.update(2)
    ma_without_window.update(3)
    assert ma_without_window.sum == 6
    assert ma_without_window.count == 3


def test_get_average_with_window(ma_with_window):
    ma_with_window.update(1)
    assert ma_with_window.get_average() == 1
    ma_with_window.update(2)
    assert ma_with_window.get_average() == 1.5
    ma_with_window.update(3)
    assert ma_with_window.get_average() == 2
    ma_with_window.update(4)
    assert ma_with_window.get_average() == 3


def test_get_average_without_window(ma_without_window):
    ma_without_window.update(1)
    assert ma_without_window.get_average() == 1
    ma_without_window.update(2)
    assert ma_without_window.get_average() == 1.5
    ma_without_window.update(3)
    assert ma_without_window.get_average() == 2


def test_reset_with_window(ma_with_window):
    ma_with_window.update(1)
    ma_with_window.update(2)
    ma_with_window.reset()
    assert len(ma_with_window.window) == 0


def test_reset_without_window(ma_without_window):
    ma_without_window.update(1)
    ma_without_window.update(2)
    ma_without_window.reset()
    assert ma_without_window.sum == 0
    assert ma_without_window.count == 0


def test_empty_average():
    ma = MovingAverage(window_size=3)
    assert ma.get_average() == 0
    ma = MovingAverage()
    assert ma.get_average() == 0


@pytest.mark.parametrize("values, expected", [
    ([1, 2, 3, 4, 5], 4),
    ([10, 20, 30], 20),
    ([1], 1),
    ([], 0)
])
def test_multiple_updates_with_window(values: List[float], expected: float):
    ma = MovingAverage(window_size=3)
    for value in values:
        ma.update(value)
    assert ma.get_average() == expected


@pytest.mark.parametrize("values, expected", [
    ([1, 2, 3, 4, 5], 3),
    ([10, 20, 30], 20),
    ([1], 1),
    ([], 0)
])
def test_multiple_updates_without_window(values: List[float], expected: float):
    ma = MovingAverage()
    for value in values:
        ma.update(value)
    assert ma.get_average() == expected
