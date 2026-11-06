"""Exercise the CI discovery guard against isolated test directories."""
import shutil
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

    def test_only_runner_self_tests_present_fails_project_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'ci').mkdir()
            (root / 'tests').mkdir()
            ci_dir = Path(__file__).resolve().parent
            for filename in ('run_unit_tests.py', 'test_run_unit_tests.py'):
                shutil.copy(ci_dir / filename, root / 'ci' / filename)
            result = subprocess.run(
                [sys.executable, '-m', 'ci.run_unit_tests'],
                cwd=root, capture_output=True, text=True, timeout=10,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No tests discovered', result.stderr)

    def test_passing_discovered_test_succeeds(self):
        result = self.run_in_directory(
            'import unittest\nclass Example(unittest.TestCase):\n'
            '    def test_ok(self): self.assertTrue(True)\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Ran 1 test', result.stderr)

    def test_all_skipped_tests_fail(self):
        result = self.run_in_directory(
            'import unittest\nclass Example(unittest.TestCase):\n'
            '    @unittest.skip("unavailable")\n'
            '    def test_skipped(self): pass\n'
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('All discovered tests were skipped', result.stderr)

    def test_skipped_class_with_no_run_tests_fails(self):
        result = self.run_in_directory(
            'import unittest\nclass Example(unittest.TestCase):\n'
            '    @classmethod\n'
            '    def setUpClass(cls): raise unittest.SkipTest("unavailable")\n'
            '    def test_skipped(self): pass\n'
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('All discovered tests were skipped', result.stderr)

    def test_skipped_class_and_passing_case_succeeds(self):
        result = self.run_in_directory(
            'import unittest\nclass Skipped(unittest.TestCase):\n'
            '    @classmethod\n'
            '    def setUpClass(cls): raise unittest.SkipTest("unavailable")\n'
            '    def test_skipped(self): pass\n'
            'class Passing(unittest.TestCase):\n'
            '    def test_ok(self): pass\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_partially_skipped_suite_succeeds(self):
        result = self.run_in_directory(
            'import unittest\nclass Example(unittest.TestCase):\n'
            '    @unittest.skip("unavailable")\n'
            '    def test_skipped(self): pass\n'
            '    def test_ok(self): pass\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('skipped=1', result.stderr)

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
