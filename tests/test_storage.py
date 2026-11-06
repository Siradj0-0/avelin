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

    def test_changing_profile_is_blocked(self):
        with patch('avelin.actions.power_profiles', return_value=(['balanced', 'performance'], 'balanced')), patch('avelin.actions.subprocess.run') as run:
            with self.assertRaisesRegex(RuntimeError, 'temporarily disabled'):
                actions.set_power_profile('performance')
            run.assert_not_called()


class StorageSafetyTests(unittest.TestCase):
    def test_empty_exact_and_exceeded_entry_limits(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            self.assertEqual(storage.measure('x', p, max_entries=0).status, 'complete')
            (p/'one').write_bytes(b'abc')
            exact = storage.measure('x', p, max_entries=1)
            self.assertEqual(exact.status, 'complete')
            self.assertEqual(exact.allocated_bytes, (p/'one').stat().st_blocks * 512)
            limited = storage.measure('x', p, max_entries=0)
            self.assertEqual(limited.status, 'partial')
            self.assertIn('entry limit', limited.note)

    def test_zero_time_and_invalid_limits(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertIn('time limit', storage.measure('x', root, seconds=0).note)
            for kwargs in ({'seconds': -1}, {'seconds': float('nan')},
                           {'seconds': float('inf')}, {'max_entries': -1},
                           {'max_entries': 1.5}, {'max_entries': True}):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    storage.measure('x', root, **kwargs)

    def test_root_and_nested_symlinks_never_followed(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            p, external = Path(root), Path(outside)
            (external/'secret').write_bytes(b'secret')
            (p/'out').symlink_to(external, target_is_directory=True)
            (p/'dangling').symlink_to(external/'missing')
            (p/'loop').symlink_to(p, target_is_directory=True)
            self.assertEqual(storage.measure('x', p/'out').status, 'unavailable')
            result = storage.measure('x', p)
            self.assertEqual((result.status, result.allocated_bytes), ('complete', 0))
            self.assertEqual((external/'secret').read_bytes(), b'secret')

    def test_nested_and_sparse_files_count_allocated_not_apparent(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            (p/'sub').mkdir()
            file = p/'sub'/'sparse'
            with file.open('wb') as f:
                f.seek(4 * 1024 * 1024)
                f.write(b'x')
            result = storage.measure('x', p)
            self.assertEqual(result.status, 'complete')
            self.assertEqual(result.allocated_bytes, file.stat().st_blocks * 512)

    def test_scanner_never_opens_regular_files_or_deletes(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            f = p/'file'
            f.write_bytes(b'unchanged')
            original = f.stat()
            real_open = os.open
            def checked_open(path, flags, *args, **kwargs):
                self.assertTrue(flags & os.O_DIRECTORY)
                self.assertTrue(flags & os.O_NOFOLLOW)
                self.assertFalse(flags & (os.O_WRONLY | os.O_RDWR | os.O_TRUNC | os.O_CREAT))
                return real_open(path, flags, *args, **kwargs)
            with patch('avelin.storage.os.open', side_effect=checked_open), \
                 patch('avelin.storage.os.unlink', side_effect=AssertionError('delete')), \
                 patch('avelin.storage.os.remove', side_effect=AssertionError('delete')):
                self.assertEqual(storage.measure('x', p).status, 'complete')
            self.assertEqual(f.read_bytes(), b'unchanged')
            self.assertEqual(f.stat().st_mtime_ns, original.st_mtime_ns)
            self.assertEqual(f.stat().st_mode, original.st_mode)

    def test_missing_block_information_is_partial_not_zero_complete(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/'f').write_text('hello')
            real_stat = os.stat
            def without_blocks(path, *args, **kwargs):
                st = real_stat(path, *args, **kwargs)
                if path == 'f' and kwargs.get('dir_fd') is not None:
                    return SimpleNamespace(st_mode=st.st_mode, st_dev=st.st_dev, st_ino=st.st_ino)
                return st
            with patch('avelin.storage.os.stat', side_effect=without_blocks):
                result = storage.measure('x', root)
            self.assertEqual((result.status, result.allocated_bytes), ('partial', 0))
            self.assertIn('allocated size unavailable', result.note)

    def test_child_stat_failure_is_partial_and_preserves_other_subtotal(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            (p/'good').write_bytes(b'good')
            (p/'bad').write_bytes(b'bad')
            expected = (p/'good').stat().st_blocks * 512
            real_stat = os.stat
            def fail_bad(path, *args, **kwargs):
                if path == 'bad' and kwargs.get('dir_fd') is not None:
                    raise PermissionError('denied')
                return real_stat(path, *args, **kwargs)
            with patch('avelin.storage.os.stat', side_effect=fail_bad):
                result = storage.measure('x', p)
            self.assertEqual((result.status, result.allocated_bytes), ('partial', expected))
            self.assertIn('access or filesystem error', result.note)

    def test_cross_device_directory_not_opened(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            (p/'mount').mkdir()
            (p/'mount'/'file').write_bytes(b'data')
            real_stat = os.stat
            def other_device(path, *args, **kwargs):
                st = real_stat(path, *args, **kwargs)
                if path == 'mount' and kwargs.get('dir_fd') is not None:
                    return SimpleNamespace(st_mode=st.st_mode, st_dev=st.st_dev + 1, st_ino=st.st_ino)
                return st
            with patch('avelin.storage.os.stat', side_effect=other_device):
                result = storage.measure('x', p)
            self.assertEqual((result.status, result.allocated_bytes), ('partial', 0))
            self.assertIn('other filesystem', result.note)

    def test_root_replacement_and_fstat_failure_close_descriptor(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as root:
            real_fstat = os.fstat
            real_close = os.close
            closed = []
            def close(fd):
                closed.append(fd)
                return real_close(fd)
            def replaced(fd):
                st = real_fstat(fd)
                return SimpleNamespace(st_dev=st.st_dev, st_ino=st.st_ino + 1)
            with patch('avelin.storage.os.fstat', side_effect=replaced), \
                 patch('avelin.storage.os.close', side_effect=close):
                result = storage.measure('x', root)
            self.assertEqual(result.status, 'unavailable')
            self.assertIn('changed', result.note)
            self.assertEqual(len(closed), 1)
            closed.clear()
            with patch('avelin.storage.os.fstat', side_effect=OSError('failure')), \
                 patch('avelin.storage.os.close', side_effect=close):
                result = storage.measure('x', root)
            self.assertEqual(result.status, 'unavailable')
            self.assertEqual(len(closed), 1)

    def test_child_replacement_is_partial_and_does_not_scan_replacement(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            (p/'child').mkdir()
            (p/'child'/'file').write_text('data')
            real_fstat = os.fstat
            calls = 0
            def replaced(fd):
                nonlocal calls
                calls += 1
                st = real_fstat(fd)
                if calls == 2:
                    return SimpleNamespace(st_dev=st.st_dev, st_ino=st.st_ino + 1)
                return st
            with patch('avelin.storage.os.fstat', side_effect=replaced):
                result = storage.measure('x', p)
            self.assertEqual((result.status, result.allocated_bytes), ('partial', 0))
            self.assertIn('directory changed', result.note)

    def test_depth_limit_is_partial(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            for _ in range(65):
                p = p/'d'
                p.mkdir()
            (p/'file').write_bytes(b'data')
            result = storage.measure('x', root)
            self.assertEqual((result.status, result.allocated_bytes), ('partial', 0))
            self.assertIn('depth limit', result.note)

    def test_directory_replaced_by_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            p, external = Path(root), Path(outside)
            (p/'child').mkdir()
            (external/'secret').write_bytes(b'secret')
            real_open = os.open
            swapped = False
            def swap_on_open(path, flags, *args, **kwargs):
                nonlocal swapped
                if path == 'child' and kwargs.get('dir_fd') is not None and not swapped:
                    swapped = True
                    (p/'child').rename(p/'moved')
                    (p/'child').symlink_to(external, target_is_directory=True)
                return real_open(path, flags, *args, **kwargs)
            with patch('avelin.storage.os.open', side_effect=swap_on_open):
                result = storage.measure('x', p)
            self.assertTrue(swapped)
            self.assertEqual(result.status, 'partial')
            self.assertEqual(result.allocated_bytes, 0)
            self.assertEqual((external/'secret').read_bytes(), b'secret')

    def test_scandir_open_failure_closes_directory_descriptor(self):
        with tempfile.TemporaryDirectory() as root:
            real_close = os.close
            closed = []
            def close(fd):
                closed.append(fd)
                return real_close(fd)
            with patch('avelin.storage.os.scandir', side_effect=PermissionError('denied')), \
                 patch('avelin.storage.os.close', side_effect=close):
                result = storage.measure('x', root)
            self.assertEqual(result.status, 'unavailable')
            self.assertEqual(len(closed), 1)

    def test_special_files_are_not_opened(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            os.mkfifo(p/'pipe')
            result = storage.measure('x', p)
            self.assertEqual((result.status, result.allocated_bytes), ('complete', 0))

    def test_absolute_xdg_locations_and_independent_roots(self):
        with tempfile.TemporaryDirectory() as root:
            cache = Path(root)/'cache'
            data = Path(root)/'data'
            cache.mkdir()
            (cache/'file').write_text('x')
            with patch.dict(os.environ, {'XDG_CACHE_HOME': str(cache), 'XDG_DATA_HOME': str(data)}):
                paths = dict(storage.locations())
                self.assertEqual(paths['Application caches'], cache)
                self.assertEqual(paths['Home trash'], data/'Trash/files')
                with patch('avelin.storage.locations', return_value=[('cache', cache), ('trash', data/'Trash/files')]):
                    results = storage.scan()
            self.assertEqual(results[0].status, 'complete')
            self.assertEqual(results[1].status, 'missing')
