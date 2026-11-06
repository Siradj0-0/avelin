import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from avelin import system, actions, updates


class MetricsTests(unittest.TestCase):
    def test_cpu_delta(self):
        self.assertEqual(system.cpu_percent((100, 25), (200, 65)), 60)
        self.assertIsNone(system.cpu_percent(None, (1, 1)))
        self.assertIsNone(system.cpu_percent((100, 25), (100, 25)))
        self.assertIsNone(system.cpu_percent((100, 25), (110, 50)))

    def test_proc_parse_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'stat').write_text('cpu 100 2 3 4 5 6 7 8 900 900\n')
            self.assertEqual(system.cpu_ticks(str(p/'stat')), (135, 9))
            (p/'mem').write_text('MemTotal: 1000 kB\nMemAvailable: 250 kB\n')
            self.assertEqual(system.memory(str(p/'mem')), (750*1024, 1000*1024))
            self.assertIsNone(system.memory(str(p/'missing')))

    def test_format(self):
        self.assertEqual(system.bytes_label(1024**3), '1.0 GiB')
        self.assertEqual(system.bytes_label(None), 'Unavailable')

    def test_zram(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'swaps'
            p.write_text('Filename Type Size Used Priority\n/dev/zram0 partition 20 1 100\n')
            self.assertEqual(system.zram_status(str(p)), 'Active')
            p.write_text('Filename Type Size Used Priority\n/swapfile file 20 1 -2\n')
            self.assertEqual(system.zram_status(str(p)), 'Not detected')


class SafetyTests(unittest.TestCase):
    def test_no_gnome_means_no_setting(self):
        with patch.dict('os.environ', {'XDG_CURRENT_DESKTOP':'KDE'}):
            self.assertIsNone(actions.setting_state('enable-animations'))
            with self.assertRaises(RuntimeError):
                actions.set_setting('enable-animations', False)

    def test_trash_uses_no_shell(self):
        with patch('avelin.actions.shutil.which', return_value='/usr/bin/gio'), patch('avelin.actions.subprocess.run') as run:
            actions.empty_trash()
            self.assertEqual(run.call_args.args[0], ['gio', 'trash', '--empty'])
            self.assertNotIn('shell', run.call_args.kwargs)

    def test_versions(self):
        self.assertEqual(updates.version('v1.2.3'), (1,2,3))
        self.assertIsNone(updates.version('1.2.3-beta'))
        self.assertIsNone(updates.version('v01.2.3'))
        self.assertIsNone(updates.version('oops'))

if __name__ == '__main__':
    unittest.main()

class UpdateTests(unittest.TestCase):
    def test_finds_numbered_prerelease_and_ignores_drafts(self):
        from unittest.mock import MagicMock
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'[{"draft":false,"tag_name":"v0.2.0","prerelease":true},{"draft":true,"tag_name":"v9.0.0"}]'
        with patch('avelin.updates.urllib.request.urlopen', return_value=response):
            status, text = updates.check_latest()
        self.assertEqual(status, 'new')
        self.assertIn('v0.2.0', text)

    def test_no_releases(self):
        from unittest.mock import MagicMock
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'[]'
        with patch('avelin.updates.urllib.request.urlopen', return_value=response):
            self.assertEqual(updates.check_latest()[0], 'none')
