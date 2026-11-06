import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from avelin.detect.os_release import distribution_name, parse_os_release, read_os_release


class OSReleaseTests(unittest.TestCase):
    def test_quoted_and_escaped_values_and_last_duplicate(self):
        fields = parse_os_release('PRETTY_NAME=First\nPRETTY_NAME="Acme \\\"Workstation\\\" \\$1"\nID=acme\nID_LIKE="debian ubuntu"\n')
        self.assertEqual(fields['PRETTY_NAME'], 'Acme "Workstation" $1')
        self.assertEqual(fields['ID_LIKE'], 'debian ubuntu')
        self.assertEqual(parse_os_release("NAME='Acme Linux'\n")['NAME'], 'Acme Linux')

    def test_no_evaluation_and_malformed_duplicate_is_not_reused(self):
        fields = parse_os_release('NAME=Safe\nNAME="$(touch /tmp/no)"\nID="unterminated\n')
        self.assertNotIn('NAME', fields)
        self.assertNotIn('ID', fields)
        self.assertIsNone(distribution_name({'PRETTY_NAME': ' '}))

    def test_fallback_and_no_merging(self):
        with tempfile.TemporaryDirectory() as d:
            etc, vendor = Path(d) / 'etc', Path(d) / 'vendor'
            vendor.write_text('PRETTY_NAME="Vendor Linux"\nID=vendor\n')
            self.assertEqual(distribution_name(read_os_release(etc, vendor)), 'Vendor Linux')
            etc.write_text('ID=local\n')
            fields = read_os_release(etc, vendor)
            self.assertEqual(fields, {'ID': 'local'})
            self.assertIsNone(distribution_name(fields))
            etc.unlink()
            vendor.unlink()
            self.assertIsNone(read_os_release(etc, vendor))

    def test_permission_error_does_not_fallback(self):
        with patch.object(Path, 'read_text', side_effect=PermissionError):
            self.assertIsNone(read_os_release('etc', 'vendor'))

    def test_invalid_utf8_is_unavailable(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'etc'
            path.write_bytes(b'NAME=\xff')
            self.assertIsNone(read_os_release(path, Path(d) / 'vendor'))


if __name__ == '__main__':
    unittest.main()
