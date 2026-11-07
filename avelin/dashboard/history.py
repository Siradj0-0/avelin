"""Bounded, process-local time series storage for dashboard samples.

Callers provide timestamps in a single monotonic clock domain. This component
is not thread-safe, does not persist data, and does not collect metrics itself.
A None value is a gap; a numeric zero is an observation.
"""
from collections import deque
import math


class History:
    """Keep at most max_series series of at most max_samples points each.

    A full registry rejects new series rather than silently evicting existing
    ones. Equal timestamps are retained in insertion order. Ranges include
    both endpoints. No interpolation or downsampling is performed.
    """

    def __init__(self, max_series=16, max_samples=300):
        if (type(max_series) is not int or not 1 <= max_series <= 64 or
                type(max_samples) is not int or not 1 <= max_samples <= 1800):
            raise ValueError('history limits out of range')
        self._max_series = max_series
        self._max_samples = max_samples
        self._series = {}

    @staticmethod
    def _name(name):
        if not isinstance(name, str) or not 1 <= len(name) <= 128:
            raise ValueError('series name must contain 1–128 characters')

    @staticmethod
    def _number(value, nonnegative=False):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('expected a finite number')
        try:
            result = float(value)
        except (OverflowError, ValueError):
            raise ValueError('expected a finite number') from None
        if not math.isfinite(result) or (nonnegative and result < 0):
            raise ValueError('expected a finite number in range')
        return result

    def append(self, name, timestamp, value):
        self._name(name)
        timestamp = self._number(timestamp, nonnegative=True)
        value = None if value is None else self._number(value)
        series = self._series.get(name)
        if series is None:
            if len(self._series) >= self._max_series:
                raise ValueError('series limit reached')
            series = deque(maxlen=self._max_samples)
            self._series[name] = series
        if series and timestamp < series[-1][0]:
            raise ValueError('timestamps must be nondecreasing')
        series.append((timestamp, value))

    def range(self, name, start, end):
        self._name(name)
        start = self._number(start, nonnegative=True)
        end = self._number(end, nonnegative=True)
        if end < start:
            raise ValueError('range end precedes start')
        return tuple(point for point in self._series.get(name, ())
                     if start <= point[0] <= end)
