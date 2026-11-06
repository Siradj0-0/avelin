import errno
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from avelin.hardware import HardwareMonitor


class HardwareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sys = self.root / 'sys'
        self.proc = self.root / 'proc'
        self.proc.mkdir()
        (self.sys / 'block').mkdir(parents=True)
        (self.sys / 'class' / 'drm').mkdir(parents=True)
        self.now = 10.0
        self.monitor = HardwareMonitor(self.sys, self.proc, self.root, {}, lambda: self.now)

    def put(self, path, text):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(text), encoding='utf-8')
        return path

    def disk(self, name='sda', dev='8:0', ticks=100, seq='1'):
        p = self.sys / 'block' / name
        self.put(p / 'dev', dev)
        self.put(p / 'diskseq', seq)
        self.put(p / 'size', '2048')
        self.put(p / 'queue' / 'rotational', '1')
        self.put(p / 'queue' / 'iostats', '1')
        self.put(p / 'device' / 'model', 'Test disk\n')
        self.stat(p, ticks)
        return p

    def stat(self, p, ticks):
        self.put(p / 'stat', f'1 2 3 4 5 6 7 8 0 {ticks} 10 11 12 13 14 15 16\n')

    def gpu(self, card='card0', driver='amdgpu', busy='42'):
        p = self.sys / 'devices' / card
        p.mkdir(parents=True)
        self.put(p / 'vendor', '0x1002')
        self.put(p / 'device', '0x1234')
        if busy is not None:
            self.put(p / 'gpu_busy_percent', busy)
        drivers = self.sys / 'drivers' / driver
        drivers.mkdir(parents=True, exist_ok=True)
        (p / 'driver').symlink_to(drivers)
        c = self.sys / 'class' / 'drm' / card
        c.mkdir()
        (c / 'device').symlink_to(p)
        return p

    def test_storage_inventory_and_two_sample_busy(self):
        p = self.disk()
        loop = self.disk('loop0', '7:0', 10, '3')
        (p / 'sda1').mkdir()  # not a second whole disk
        first = self.monitor.sample()
        self.assertEqual([x.name for x in first.storage], ['loop0', 'sda'])
        disk = first.storage[1]
        self.assertEqual((disk.device_number.value, disk.model.value), ('8:0', 'Test disk'))
        self.assertEqual((disk.size_bytes.value, disk.rotational.value), (1048576, 1))
        self.assertEqual(disk.busy_percent.status, 'warming_up')
        self.now += 2
        self.stat(p, 600)
        self.stat(loop, 10)
        result = self.monitor.sample().storage
        self.assertEqual(result[1].busy_percent.value, 25.0)
        self.assertEqual(result[0].busy_percent.value, 0.0)
        self.assertEqual(result[1].busy_percent.status, 'ok')

    def test_counter_reset_invalid_interval_and_recovery(self):
        p = self.disk(ticks=100)
        self.monitor.sample()
        self.now += 1
        self.stat(p, 99)
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'counter_reset')
        self.stat(p, 100)
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'invalid')
        self.now += 1
        self.stat(p, 2200)
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'invalid')
        self.now += 2
        self.stat(p, 2300)
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.value, 5.0)

    def test_device_identity_and_disappearance(self):
        p = self.disk()
        self.monitor.sample()
        self.now += 1
        self.put(p / 'diskseq', '2')
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'warming_up')
        self.now += 1
        self.put(p / 'dev', '8:16')
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'warming_up')
        self.now += 1
        self.put(p / 'dev', 'bad')
        disk = self.monitor.sample().storage[0]
        self.assertEqual(disk.device_number.status, 'invalid')
        self.assertEqual(disk.busy_percent.status, 'unavailable')
        self.put(p / 'dev', '8:16')
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'warming_up')
        (p / 'stat').unlink()
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'unavailable')
        self.stat(p, 100)
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'warming_up')

    def test_invalid_and_missing_values_are_not_zero(self):
        p = self.disk()
        self.put(p / 'size', '-1')
        self.put(p / 'queue' / 'rotational', '2')
        self.put(p / 'stat', '1 2 nope')
        (p / 'device' / 'model').unlink()
        disk = self.monitor.sample().storage[0]
        for reading, status in [(disk.size_bytes, 'invalid'), (disk.rotational, 'invalid'),
                                (disk.busy_percent, 'invalid'), (disk.model, 'unavailable')]:
            self.assertIsNone(reading.value)
            self.assertEqual(reading.status, status)
        self.put(p / 'size', '0')
        self.assertEqual(self.monitor.sample().storage[0].size_bytes.value, 0)
        self.put(p / 'size', '9' * 5000)
        self.assertEqual(self.monitor.sample().storage[0].size_bytes.status, 'invalid')

    def test_disabled_or_missing_accounting_breaks_baseline(self):
        p = self.disk()
        self.monitor.sample()
        self.now += 1
        self.put(p / 'queue' / 'iostats', '0')
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'unavailable')
        self.put(p / 'queue' / 'iostats', '1')
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'warming_up')
        (p / 'queue' / 'iostats').unlink()
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'unavailable')

    def test_multiple_gpu_drivers_and_dedup(self):
        amd = self.gpu()
        self.gpu('card1', 'i915', '90')
        self.gpu('card2', 'nvidia', '90')
        drm = self.sys / 'class' / 'drm'
        (drm / 'card0-HDMI-A-1').mkdir()
        (drm / 'renderD128').mkdir()
        (drm / 'card3').mkdir()
        (drm / 'card3' / 'device').symlink_to(amd)
        snap = self.monitor.sample()
        self.assertEqual(snap.gpu_status, 'ok')
        self.assertEqual([x.name for x in snap.gpus], ['card0', 'card1', 'card2'])
        self.assertEqual(snap.gpus[0].busy_percent.value, 42)
        self.assertEqual(snap.gpus[0].vendor_id.value, '0x1002')
        self.assertEqual(snap.gpus[0].kind.status, 'unavailable')
        for gpu in snap.gpus[1:]:
            self.assertEqual(gpu.busy_percent.status, 'unavailable')
            self.assertIsNone(gpu.busy_percent.value)

    def test_amd_bad_busy_and_missing_driver(self):
        p = self.gpu(busy='101')
        self.assertEqual(self.monitor.sample().gpus[0].busy_percent.status, 'invalid')
        self.put(p / 'gpu_busy_percent', '-1')
        self.assertEqual(self.monitor.sample().gpus[0].busy_percent.status, 'invalid')
        self.put(p / 'gpu_busy_percent', '0')
        self.assertEqual(self.monitor.sample().gpus[0].busy_percent.value, 0)
        (p / 'gpu_busy_percent').unlink()
        self.assertEqual(self.monitor.sample().gpus[0].busy_percent.status, 'unavailable')
        (p / 'driver').unlink()
        self.assertEqual(self.monitor.sample().gpus[0].busy_percent.status, 'unavailable')

    def test_sandbox_and_unavailable_enumeration(self):
        (self.sys / 'block').rmdir()
        self.assertEqual(self.monitor.sample().storage_status, 'unavailable')
        self.put(self.root / '.flatpak-info', '[Application]')
        snap = self.monitor.sample()
        self.assertTrue(snap.sandbox)
        self.assertEqual(snap.storage_status, 'sandbox')
        self.assertEqual(snap.gpu_status, 'ok')
        (self.root / '.flatpak-info').unlink()
        self.assertTrue(HardwareMonitor(self.sys, self.proc, self.root, {'SNAP': '/snap/foo'}).sample().sandbox)
        self.assertFalse(self.monitor.sample().sandbox)

    def test_permissions_are_distinct_even_in_sandbox(self):
        p = self.disk()
        self.put(self.root / '.flatpak-info', 'x')
        original = Path.open
        def restricted(path, *args, **kwargs):
            if path == p / 'size':
                raise PermissionError(errno.EACCES, 'denied', str(path))
            return original(path, *args, **kwargs)
        with patch.object(Path, 'open', restricted):
            reading = self.monitor.sample().storage[0].size_bytes
        self.assertEqual(reading.status, 'permission')
        self.assertIsNone(reading.value)
        self.assertEqual(str(p / 'size'), reading.source)
        with patch.object(Path, 'iterdir', side_effect=PermissionError(errno.EPERM, 'denied')):
            snap = self.monitor.sample()
        self.assertEqual((snap.storage_status, snap.gpu_status), ('permission', 'permission'))

    def test_partial_gpu_disappearance(self):
        self.gpu()
        card = self.sys / 'class' / 'drm' / 'card1'
        card.mkdir()
        (card / 'device').symlink_to(self.root / 'missing')
        snap = self.monitor.sample()
        self.assertEqual(len(snap.gpus), 1)
        self.assertEqual(snap.gpu_status, 'unavailable')

    def test_gpu_permission_and_malformed_attributes(self):
        p = self.gpu()
        original = Path.open
        def restricted(path, *args, **kwargs):
            if path == self.sys / 'class' / 'drm' / 'card0' / 'device' / 'gpu_busy_percent':
                raise PermissionError(errno.EACCES, 'denied', str(path))
            return original(path, *args, **kwargs)
        with patch.object(Path, 'open', restricted):
            gpu = self.monitor.sample().gpus[0]
        self.assertEqual(gpu.busy_percent.status, 'permission')
        self.assertIsNone(gpu.busy_percent.value)
        (p / 'vendor').write_bytes(b'\xff')
        self.assertEqual(self.monitor.sample().gpus[0].vendor_id.status, 'invalid')

    def test_unreadable_interval_cannot_bridge_storage_samples(self):
        p = self.disk()
        self.monitor.sample()
        original = Path.open
        def restricted(path, *args, **kwargs):
            if path == p / 'stat':
                raise PermissionError(errno.EACCES, 'denied', str(path))
            return original(path, *args, **kwargs)
        self.now += 1
        with patch.object(Path, 'open', restricted):
            reading = self.monitor.sample().storage[0].busy_percent
        self.assertEqual(reading.status, 'permission')
        self.now += 1
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'warming_up')

    def test_missing_diskseq_still_samples_and_changed_diskseq_warms_up(self):
        p = self.disk()
        (p / 'diskseq').unlink()
        self.monitor.sample()
        self.now += 1
        self.stat(p, 200)
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.value, 10.0)
        self.put(p / 'diskseq', '3')
        self.now += 1
        self.assertEqual(self.monitor.sample().storage[0].busy_percent.status, 'warming_up')

    def test_no_commands_or_writes_during_sampling(self):
        self.disk()
        self.gpu()
        before = {p: p.read_bytes() for p in self.sys.rglob('*') if p.is_file()}
        with patch('subprocess.run', side_effect=AssertionError('command executed')), \
             patch('os.system', side_effect=AssertionError('shell executed')):
            self.monitor.sample()
        after = {p: p.read_bytes() for p in self.sys.rglob('*') if p.is_file()}
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
