"""Exercise proc parsers using disposable, synthetic text fixtures."""
import tempfile
import unittest
from pathlib import Path

from avelin import system


class ProcInputRegressionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'proc-fixture'

    def memory_from(self, text):
        self.path.write_text(text, encoding='utf-8')
        return system.memory(self.path)

    def ticks_from(self, text):
        self.path.write_text(text, encoding='utf-8')
        return system.cpu_ticks(self.path)

    def test_memory_accepts_valid_kibibyte_fields(self):
        self.assertEqual(self.memory_from('MemTotal: 100 kB\nMemAvailable: 25 kB\n'),
                         (75 * 1024, 100 * 1024))

    def test_memory_missing_or_invalid_fields_are_unavailable(self):
        for text in ('', 'MemTotal: 100 kB\n', 'MemAvailable: 25 kB\n',
                     'MemTotal: 100 kB\nMemAvailable: -1 kB\n',
                     'MemTotal: 100 kB\nMemAvailable: nope kB\n',
                     'MemTotal: 0 kB\nMemAvailable: 0 kB\n'):
            with self.subTest(text=text):
                self.assertIsNone(self.memory_from(text))

    def test_memory_rejects_non_kb_units_and_unit_suffixes(self):
        for unit in ('bytes', 'MB', 'kBytes', 'kBgarbage'):
            with self.subTest(unit=unit):
                self.assertIsNone(self.memory_from(
                    f'MemTotal: 100 {unit}\nMemAvailable: 25 {unit}\n'))

    def test_oversized_numeric_memory_is_unavailable(self):
        text = 'MemTotal: ' + '9' * 5000 + ' kB\nMemAvailable: 25 kB\n'
        self.assertIsNone(self.memory_from(text))

    def test_cpu_truncated_and_malformed_records_are_unavailable(self):
        for text in ('', 'cpu\n', 'cpu 1 2 3\n', 'cpu0 1 2 3 4\n',
                     'cpu 1 2 invalid 4\n', 'cpu 1 2 3 4 bad\n'):
            with self.subTest(text=text):
                self.assertIsNone(self.ticks_from(text))

    def test_cpu_accepts_short_valid_and_full_records(self):
        self.assertEqual(self.ticks_from('cpu 1 2 3 4\n'), (10, 4))
        self.assertEqual(self.ticks_from('cpu 1 2 3 4 5 6 7 8 90 91\n'),
                         (36, 9))


if __name__ == '__main__':
    unittest.main()
