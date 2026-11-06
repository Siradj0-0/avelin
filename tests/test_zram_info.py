import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from avelin import zram_info


class ZramInfoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.proc = self.root / 'proc'
        self.sys = self.root / 'sys'
        (self.sys / 'block').mkdir(parents=True)
        self.write('proc/swaps', 'Filename Type Size Used Priority\n')
        self.write('sys/module/zswap/parameters/enabled', 'N\n')
        self.write('sys/power/state', 'freeze mem disk\n')
        self.write('sys/power/resume', '0:0\n')
        self.write('sys/power/resume_offset', '0\n')

    def write(self, path, content):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def collect(self):
        return zram_info.collect(proc_root=self.proc, sys_root=self.sys)

    def test_empty_known_observations(self):
        result = self.collect()
        self.assertEqual(result.swaps, ())
        self.assertEqual(result.devices, ())
        self.assertIs(result.zswap_enabled, False)
        self.assertIn('disk', result.power_states)
        self.assertEqual(result.resume_device, '0:0')
        self.assertEqual(result.resume_offset, 0)
        self.assertEqual(result.issues, ())

    def test_multiple_devices_and_swap_units(self):
        self.write('proc/swaps', 'Filename Type Size Used Priority\n/dev/zram0 partition 100 5 100\n/swap\\040file file 200 1 -2\n')
        for name in ('zram0', 'zram10'):
            self.write(f'sys/block/{name}/disksize', '102400')
            self.write(f'sys/block/{name}/comp_algorithm', 'lzo [zstd] lz4')
            self.write(f'sys/block/{name}/mm_stat', '8192 4096 6000 0 0 0 0 0 0')
        (self.sys / 'block' / 'zram-control').mkdir()
        r = self.collect()
        self.assertEqual([d.name for d in r.devices], ['zram0', 'zram10'])
        self.assertEqual((r.devices[0].original_bytes, r.devices[0].compressed_bytes, r.devices[0].memory_bytes), (8192, 4096, 6000))
        self.assertEqual((r.devices[0].algorithm, r.devices[0].algorithms), ('zstd', ('lzo', 'zstd', 'lz4')))
        self.assertEqual((r.swaps[0].size_bytes, r.swaps[0].used_bytes, r.swaps[0].priority), (102400, 5120, 100))
        self.assertTrue(r.swaps[0].is_canonical_zram_path)
        self.assertEqual(r.swaps[1].path, '/swap file')
        self.assertFalse(r.swaps[1].is_canonical_zram_path)
        self.assertEqual(r.issues, ())

    def test_unavailable_does_not_mean_disabled_or_empty(self):
        (self.proc / 'swaps').unlink()
        (self.sys / 'module/zswap/parameters/enabled').unlink()
        (self.sys / 'block').rmdir()
        r = self.collect()
        self.assertIsNone(r.swaps)
        self.assertIsNone(r.devices)
        self.assertIsNone(r.zswap_enabled)
        self.assertEqual(len(r.issues), 3)

    def test_malformed_and_partial_device(self):
        self.write('proc/swaps', 'Filename Type Size Used Priority\n/dev/zram0 partition bad 0 1\n')
        self.write('sys/module/zswap/parameters/enabled', 'maybe')
        self.write('sys/block/zram0/disksize', '-1')
        self.write('sys/block/zram0/comp_algorithm', '[lzo] [zstd]')
        self.write('sys/block/zram0/mm_stat', '1 bad 3')
        self.write('sys/power/resume', 'broken')
        self.write('sys/power/resume_offset', 'bad')
        r = self.collect()
        self.assertIsNone(r.swaps)
        self.assertIsNone(r.zswap_enabled)
        self.assertIsNone(r.devices[0].disksize_bytes)
        self.assertIsNone(r.devices[0].algorithm)
        self.assertIsNone(r.devices[0].memory_bytes)
        self.assertIsNone(r.resume_device)
        self.assertIsNone(r.resume_offset)
        self.assertEqual(len(r.issues), 7)

    def test_missing_device_attributes_are_partial(self):
        (self.sys / 'block/zram1').mkdir()
        r = self.collect()
        self.assertEqual(r.devices[0].name, 'zram1')
        self.assertIsNone(r.devices[0].disksize_bytes)
        self.assertEqual(len(r.issues), 3)

    def test_missing_header_and_permission_error(self):
        self.write('proc/swaps', '')
        r = self.collect()
        self.assertIsNone(r.swaps)
        with patch.object(Path, 'open', side_effect=PermissionError):
            r = self.collect()
        self.assertIsNone(r.swaps)
        self.assertIsNone(r.zswap_enabled)
        self.assertGreaterEqual(len(r.issues), 5)

    def test_hot_add_is_never_read_and_no_host_processes(self):
        hot_add = self.sys / 'class/zram-control/hot_add'
        self.write('sys/class/zram-control/hot_add', 'danger')
        original = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, hot_add)
            self.assertNotIn('w', args[0] if args else kwargs.get('mode', 'r'))
            return original(path, *args, **kwargs)
        with patch.object(Path, 'open', guarded), patch('os.system', side_effect=AssertionError), patch('subprocess.run', side_effect=AssertionError):
            self.collect()
        self.assertEqual(hot_add.read_text(), 'danger')

    def test_non_zram_alias_is_not_assumed(self):
        self.write('proc/swaps', 'Filename Type Size Used Priority\n/dev/disk/by-id/zram0 partition 1 0 1\n')
        self.assertFalse(self.collect().swaps[0].is_canonical_zram_path)


if __name__ == '__main__':
    unittest.main()
