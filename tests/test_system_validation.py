"""Metric availability and percentage-denominator contracts."""
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import tempfile

from avelin import system


class MemoryValidationTests(TestCase):
    def read_memory(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'meminfo'
            path.write_text(text)
            return system.memory(str(path))

    def test_valid_memory_including_zero_and_full_usage(self):
        self.assertEqual(self.read_memory('MemTotal: 100 kB\nMemAvailable: 25 kB\n'), (75 * 1024, 100 * 1024))
        self.assertEqual(self.read_memory('MemTotal: 100 kB\nMemAvailable: 100 kB\n'), (0, 100 * 1024))
        self.assertEqual(self.read_memory('MemTotal: 100 kB\nMemAvailable: 0 kB\n'), (100 * 1024, 100 * 1024))

    def test_inconsistent_memory_is_unavailable(self):
        self.assertIsNone(self.read_memory('MemTotal: 100 kB\nMemAvailable: 101 kB\n'))

    def test_missing_or_invalid_memory_is_unavailable(self):
        for text in ('', 'MemTotal: 100 kB\n', 'MemAvailable: 25 kB\n',
                     'MemTotal: 0 kB\nMemAvailable: 0 kB\n',
                     'MemTotal: 100 kB\nMemAvailable: invalid kB\n'):
            with self.subTest(text=text):
                self.assertIsNone(self.read_memory(text))
        self.assertIsNone(system.memory('/a/path/that/does/not/exist/meminfo'))


class DiskValidationTests(TestCase):
    def test_zero_total_is_unavailable(self):
        with patch.object(system.shutil, 'disk_usage', return_value=SimpleNamespace(used=0, total=0)):
            self.assertIsNone(system.disk())

    def test_valid_zero_used_is_not_unavailable(self):
        with patch.object(system.shutil, 'disk_usage', return_value=SimpleNamespace(used=0, total=100)):
            self.assertEqual(system.disk(), (0, 100))

    def test_normal_disk_and_missing(self):
        with patch.object(system.shutil, 'disk_usage', return_value=SimpleNamespace(used=40, total=100)) as disk_usage:
            self.assertEqual(system.disk('/example'), (40, 100))
            disk_usage.assert_called_once_with('/example')
        with patch.object(system.shutil, 'disk_usage', side_effect=OSError):
            self.assertIsNone(system.disk('/missing'))
