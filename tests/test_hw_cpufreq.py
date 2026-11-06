import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from avelin.hw.cpufreq import CpuPolicy, read_cpu_policies


class CpuPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def add(self, name, **fields):
        directory = self.root / name
        directory.mkdir()
        for key, value in fields.items():
            (directory / key).write_text(value)
        return directory

    def test_empty_and_unavailable(self):
        self.assertEqual(read_cpu_policies(self.root), ())
        self.assertIsNone(read_cpu_policies(self.root / 'missing'))
        with patch.object(Path, 'iterdir', side_effect=PermissionError):
            self.assertIsNone(read_cpu_policies(self.root))

    def test_distinct_policies(self):
        self.add('policy0', scaling_governor='schedutil', scaling_driver='acpi-cpufreq', related_cpus='0 1')
        self.add('policy2', scaling_governor='powersave', scaling_driver='intel_pstate', related_cpus='2 3')
        self.add('other')
        self.assertEqual(read_cpu_policies(self.root), (
            CpuPolicy('policy0', 'schedutil', 'acpi-cpufreq', (0, 1)),
            CpuPolicy('policy2', 'powersave', 'intel_pstate', (2, 3))))

    def test_missing_invalid_and_hotplug(self):
        directory = self.add('policy0', related_cpus='0-3')
        self.assertEqual(read_cpu_policies(self.root), (CpuPolicy('policy0', None, None, None),))
        for value in ('-1', 'x', '١', '9' * 5000):
            (directory / 'related_cpus').write_text(value)
            self.assertIsNone(read_cpu_policies(self.root)[0].related_cpus)
        with patch.object(Path, 'read_text', side_effect=FileNotFoundError):
            self.assertEqual(read_cpu_policies(self.root), (CpuPolicy('policy0', None, None, None),))


if __name__ == '__main__':
    unittest.main()
