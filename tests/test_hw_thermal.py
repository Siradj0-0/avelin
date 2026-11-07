import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from avelin.hw.thermal import ThermalChannel, ThermalInventory, read_thermal_channels


class ThermalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def add(self, dirname, **attributes):
        path = self.root / dirname
        path.mkdir()
        for key, value in attributes.items():
            (path / key).write_text(value)
        return path

    def test_empty_vs_unavailable(self):
        self.assertIsNone(read_thermal_channels(self.root / 'missing'))
        self.assertEqual(read_thermal_channels(self.root), ThermalInventory((), True))
        with patch.object(Path, 'iterdir', side_effect=PermissionError):
            self.assertIsNone(read_thermal_channels(self.root))

    def test_labels_unlabeled_and_signed_values(self):
        self.add('hwmon0', name='chip', temp1_input='42000', temp1_label='Package',
                 temp2_input='-500', temp0_input='99', temp1_max='100000')
        self.assertEqual(read_thermal_channels(self.root), ThermalInventory((
            ThermalChannel('hwmon0', 'chip', 1, 'Package', 42000),
            ThermalChannel('hwmon0', 'chip', 2, None, -500)), True))

    def test_malformed_and_large_numbers(self):
        device = self.add('hwmon0', temp1_input='invalid')
        for text in ('no', '1.5', '9' * 5000, '١'):
            (device / 'temp1_input').write_text(text)
            self.assertIsNone(read_thermal_channels(self.root).channels[0].raw_input)

    def test_removal_and_unreadable_device(self):
        device = self.add('hwmon0', name='chip', temp1_input='0')
        original_read = Path.read_text
        def read(path, *args, **kwargs):
            if path.name == 'temp1_input':
                raise FileNotFoundError('removed')
            return original_read(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            self.assertIsNone(read_thermal_channels(self.root).channels[0].raw_input)
        original_iter = Path.iterdir
        def walk(path):
            if path == device:
                raise PermissionError
            return original_iter(path)
        with patch.object(Path, 'iterdir', walk):
            self.assertEqual(read_thermal_channels(self.root), ThermalInventory((), False))


if __name__ == '__main__':
    unittest.main()
