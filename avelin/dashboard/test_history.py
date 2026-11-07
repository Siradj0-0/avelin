"""Deterministic tests for bounded in-memory dashboard history."""
import math
import unittest

from .history import History


class HistoryTests(unittest.TestCase):
    def test_eviction_range_boundaries_and_gap_vs_zero(self):
        history = History(max_series=2, max_samples=3)
        for t, value in [(1, 20), (2, None), (3, 0), (4, 25)]:
            history.append('cpu', t, value)
        self.assertEqual(history.range('cpu', 2, 4), ((2.0, None), (3.0, 0.0), (4.0, 25.0)))
        self.assertEqual(history.range('cpu', 3, 3), ((3.0, 0.0),))
        self.assertEqual(history.range('missing', 0, 10), ())

    def test_series_cap_does_not_evict_existing_series(self):
        history = History(max_series=1, max_samples=2)
        history.append('cpu', 1, 2)
        with self.assertRaises(ValueError):
            history.append('memory', 2, 3)
        self.assertEqual(history.range('cpu', 0, 3), ((1.0, 2.0),))

    def test_rejects_unordered_or_invalid_input_without_mutation(self):
        history = History(max_series=2, max_samples=2)
        history.append('cpu', 2, 5)
        for timestamp, value in [(1, 1), (math.nan, 1), (math.inf, 1), (-1, 1),
                                 (3, math.nan), (3, math.inf), (3, True)]:
            with self.subTest(timestamp=timestamp, value=value):
                with self.assertRaises(ValueError):
                    history.append('cpu', timestamp, value)
        self.assertEqual(history.range('cpu', 0, 10), ((2.0, 5.0),))
        history.append('cpu', 2, 6)  # equal timestamps are allowed, in insertion order
        self.assertEqual(history.range('cpu', 2, 2), ((2.0, 5.0), (2.0, 6.0)))

    def test_invalid_limits_identifiers_and_ranges(self):
        for kwargs in ({'max_series': 0}, {'max_samples': -1}, {'max_series': True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                History(**kwargs)
        history = History()
        for name in ('', 'x' * 129, None):
            with self.subTest(name=name), self.assertRaises(ValueError):
                history.append(name, 1, 1)
        for start, end in [(2, 1), (math.nan, 2), (-1, 2)]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                history.range('cpu', start, end)


if __name__ == '__main__':
    unittest.main()
