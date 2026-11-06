import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from avelin import actions, storage


class AuditTests(unittest.TestCase):
    def test_missing_and_non_directory(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(storage.measure('x', Path(root)/'missing').status, 'missing')
            p = Path(root)/'file'
            p.write_bytes(b'x')
            self.assertEqual(storage.measure('x', p).status, 'unavailable')

    def test_counts_files_but_not_symlink_or_hardlink_twice(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            p = Path(root)
            data = p/'data'
            data.write_bytes(b'a' * 4000)
            (p/'hard').hardlink_to(data)
            other = Path(outside)/'external'
            other.write_bytes(b'x' * 10000)
            (p/'link').symlink_to(other)
            result = storage.measure('x', p)
            self.assertEqual(result.status, 'complete')
            self.assertEqual(result.allocated_bytes, data.stat().st_blocks * 512)

    def test_limit_is_partial(self):
        with tempfile.TemporaryDirectory() as root:
            for i in range(3):
                (Path(root)/str(i)).write_text('a')
            self.assertEqual(storage.measure('x', root, max_entries=1).status, 'partial')

    def test_relative_xdg_paths_are_not_used(self):
        with patch.dict(os.environ, {'XDG_CACHE_HOME': 'relative', 'XDG_DATA_HOME': 'relative'}):
            paths = dict(storage.locations())
            self.assertEqual(paths['Application caches'], Path.home()/'.cache')
            self.assertEqual(paths['Home trash'], Path.home()/'.local/share/Trash/files')

    def test_rejects_unapproved_setting(self):
        with self.assertRaises(ValueError):
            actions.set_setting('arbitrary-key', True)

    def test_allowlisted_setting_updates_and_verifies(self):
        with patch('avelin.actions.setting_state', side_effect=[True, False]), patch('avelin.actions.subprocess.run') as run:
            actions.set_setting('enable-animations', False)
            self.assertEqual(run.call_args.args[0], ['gsettings', 'set', actions.SCHEMA, 'enable-animations', 'false'])
            self.assertNotIn('shell', run.call_args.kwargs)

class PowerTests(unittest.TestCase):
    def test_discovery_and_current(self):
        from unittest.mock import Mock
        listing = Mock(stdout='  performance:\n    Driver: platform\n* balanced:\n    Driver: platform\n  power-saver:\n')
        current = Mock(stdout='balanced\n')
        with patch('avelin.actions.shutil.which', return_value='/bin/powerprofilesctl'), patch('avelin.actions.subprocess.run', side_effect=[listing, current]):
            self.assertEqual(actions.power_profiles(), (['performance', 'balanced', 'power-saver'], 'balanced'))

    def test_reject_unavailable_or_arbitrary_profile(self):
        with self.assertRaises(ValueError):
            actions.set_power_profile('performance; whoami')
        with patch('avelin.actions.power_profiles', return_value=(['balanced'], 'balanced')):
            with self.assertRaises(RuntimeError):
                actions.set_power_profile('performance')

    def test_set_and_verify(self):
        with patch('avelin.actions.power_profiles', side_effect=[(['balanced','performance'],'balanced'), (['balanced','performance'],'performance')]), patch('avelin.actions.subprocess.run') as run:
            actions.set_power_profile('performance')
            self.assertEqual(run.call_args.args[0], ['powerprofilesctl', 'set', 'performance'])
