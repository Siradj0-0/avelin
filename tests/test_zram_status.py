"""Zram status must not infer absence from invalid swap observations."""
import tempfile
import unittest
from pathlib import Path

from avelin import system


class ZramStatusTests(unittest.TestCase):
    def status(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'swaps'
            path.write_text(text, encoding='utf-8')
            return system.zram_status(str(path))

    def test_missing_and_malformed_data_are_unavailable(self):
        self.assertEqual(system.zram_status('/nonexistent/avelin/swaps'), 'Unavailable')
        for text in ('', 'garbage\n', 'Filename Type Size Used Priority\n/dev/zram0\n',
                     'Filename Type Size Used Priority\n/swapfile file bad 0 -2\n',
                     'Filename Type Size Used Priority\n/dev/zram0 partition 20 1 100\ninvalid\n'):
            with self.subTest(text=text):
                self.assertEqual(self.status(text), 'Unavailable')

    def test_only_canonical_zram_devices_are_detected(self):
        header = 'Filename Type Size Used Priority\n'
        self.assertEqual(self.status(header), 'Not detected')
        self.assertEqual(self.status(header + '/dev/zram0 partition 20 1 100\n'), 'Active')
        self.assertEqual(self.status(header + '/dev/zram0 file 20 1 -2\n'), 'Not detected')
        self.assertEqual(self.status(header + '/swapfile file 20 1 -2\n/dev/zram12 partition 30 0 5\n'), 'Active')
        for path in ('/tmp/dev/zram-backup', '/dev/zram', '/dev/zram0extra'):
            with self.subTest(path=path):
                self.assertEqual(self.status(header + f'{path} file 20 1 -2\n'), 'Not detected')
