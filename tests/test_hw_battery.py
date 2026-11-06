import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from avelin.hw.battery import Battery, BatteryInventory, read_batteries


class BatteryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def add(self, name, **attributes):
        path = self.root / name
        path.mkdir()
        for key, value in attributes.items():
            (path / key).write_text(value)
        return path

    def test_absent_directory_vs_empty_and_ac_only(self):
        self.assertIsNone(read_batteries(self.root / 'missing'))
        self.assertEqual(read_batteries(self.root), BatteryInventory((), True))
        self.add('AC', type='Mains')
        self.assertEqual(read_batteries(self.root), BatteryInventory((), True))

    def test_multiple_batteries_and_zero(self):
        self.add('BAT0', type='Battery', present='1', status='Discharging', capacity='0')
        self.add('BAT1', type='Battery', capacity='99')
        self.assertEqual(read_batteries(self.root), BatteryInventory((
            Battery('BAT0', True, 'Discharging', 0), Battery('BAT1', None, None, 99)), True))

    def test_missing_and_invalid_attributes(self):
        battery = self.add('BAT0', type='Battery', status='', capacity='101')
        self.assertEqual(read_batteries(self.root).batteries[0], Battery('BAT0', None, None, None))
        for invalid in ('-1', '1.0', 'abc', '١', '9' * 5000):
            (battery / 'capacity').write_text(invalid)
            self.assertIsNone(read_batteries(self.root).batteries[0].capacity_percent)
        (battery / 'present').write_text('0')
        (battery / 'capacity').write_text('55')
        self.assertEqual(read_batteries(self.root).batteries[0], Battery('BAT0', False, None, None))

    def test_missing_type_marks_inventory_incomplete(self):
        self.add('unknown')
        self.assertEqual(read_batteries(self.root), BatteryInventory((), False))

    def test_permission_and_removal_are_not_fabricated(self):
        self.add('BAT0', type='Battery', present='1', capacity='50')
        original = Path.read_text
        def read(path, *args, **kwargs):
            if path.name == 'capacity':
                raise FileNotFoundError('removed')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            self.assertIsNone(read_batteries(self.root).batteries[0].capacity_percent)
        with patch.object(Path, 'iterdir', side_effect=PermissionError):
            self.assertIsNone(read_batteries(self.root))


if __name__ == '__main__':
    unittest.main()
