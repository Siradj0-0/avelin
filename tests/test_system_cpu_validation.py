"""Validation of /proc/stat CPU counters; no live system data is needed."""
import tempfile
import unittest
from pathlib import Path
from avelin import system


class CpuCounterValidationTests(unittest.TestCase):
    def test_negative_counters_are_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stat'
            for index in range(8):
                values = [10] * 8
                values[index] = -1
                with self.subTest(counter=index):
                    path.write_text('cpu ' + ' '.join(map(str, values)) + '\n')
                    self.assertIsNone(system.cpu_ticks(path))

    def test_guest_fields_are_not_double_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stat'
            path.write_text('cpu 100 2 3 4 5 6 7 8 900 901\n')
            self.assertEqual(system.cpu_ticks(path), (135, 9))

    def test_missing_short_and_nonnumeric_records_are_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stat'
            self.assertIsNone(system.cpu_ticks(path))
            for record in ('', 'cpu 1 2 3', 'cpu 1 2 invalid 4', 'cpu0 1 2 3 4'):
                with self.subTest(record=record):
                    path.write_text(record + '\n')
                    self.assertIsNone(system.cpu_ticks(path))

    def test_invalid_sample_cannot_become_a_usage_percentage(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stat'
            path.write_text('cpu 100 2 3 -1 5 6 7 8\n')
            self.assertIsNone(system.cpu_percent((10, 2), system.cpu_ticks(path)))


if __name__ == '__main__':
    unittest.main()
