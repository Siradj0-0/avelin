"""Exercise the CI discovery guard against isolated test directories."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CiRunnerTests(unittest.TestCase):
    def run_in_directory(self, contents=None):
        with tempfile.TemporaryDirectory() as directory:
            if contents is not None:
                Path(directory, 'test_example.py').write_text(contents, encoding='utf-8')
            return subprocess.run(
                [sys.executable, '-m', 'ci.run_unit_tests', directory],
                capture_output=True, text=True, timeout=10,
            )

    def test_empty_discovery_fails(self):
        result = self.run_in_directory()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No tests discovered', result.stderr)

    def test_passing_discovered_test_succeeds(self):
        result = self.run_in_directory(
            'import unittest\nclass Example(unittest.TestCase):\n'
            '    def test_ok(self): self.assertTrue(True)\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Ran 1 test', result.stderr)

    def test_failing_discovered_test_fails(self):
        result = self.run_in_directory(
            'import unittest\nclass Example(unittest.TestCase):\n'
            '    def test_bad(self): self.fail("intentional failure")\n'
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('intentional failure', result.stderr)

    def test_import_failure_fails(self):
        result = self.run_in_directory('raise ImportError("intentional import failure")\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('intentional import failure', result.stderr)


if __name__ == '__main__':
    unittest.main()
