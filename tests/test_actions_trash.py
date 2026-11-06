"""Tests for failure reporting without invoking gio or deleting files."""
import os
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from avelin import actions


class EmptyTrashFailureTests(unittest.TestCase):
    def test_unavailable_gio_does_not_start_command(self):
        with patch('avelin.actions.shutil.which', return_value=None), \
             patch('avelin.actions.subprocess.run') as run:
            with self.assertRaisesRegex(RuntimeError, 'gio command is not installed'):
                actions.empty_trash()
            run.assert_not_called()

    def test_gio_removed_after_preflight_fails_without_retry(self):
        failure = FileNotFoundError('gio disappeared before launch')
        with patch('avelin.actions.shutil.which', return_value='/usr/bin/gio'), \
             patch('avelin.actions.subprocess.run', side_effect=failure) as run:
            with self.assertRaises(FileNotFoundError) as raised:
                actions.empty_trash()
        self.assertIs(raised.exception, failure)
        run.assert_called_once()

    def test_timeout_warns_about_possible_partial_deletion(self):
        failure = subprocess.TimeoutExpired(['gio', 'trash', '--empty'], 180)
        with patch('avelin.actions.shutil.which', return_value='/usr/bin/gio'), \
             patch('avelin.actions.subprocess.run', side_effect=failure) as run:
            with self.assertRaises(RuntimeError) as raised:
                actions.empty_trash()
        self.assertIs(raised.exception.__cause__, failure)
        self.assertIn('timed out', str(raised.exception))
        self.assertIn('may already have been permanently deleted', str(raised.exception))
        self.assertIn('check the trash', str(raised.exception))
        run.assert_called_once_with(
            ['gio', 'trash', '--empty'], check=True, timeout=180,
            capture_output=True,
        )

    def test_nonzero_exit_warns_about_possible_partial_deletion(self):
        failure = subprocess.CalledProcessError(1, ['gio', 'trash', '--empty'])
        with patch('avelin.actions.shutil.which', return_value='/usr/bin/gio'), \
             patch('avelin.actions.subprocess.run', side_effect=failure) as run:
            with self.assertRaises(RuntimeError) as raised:
                actions.empty_trash()
        self.assertIs(raised.exception.__cause__, failure)
        self.assertIn('gio reported an error', str(raised.exception))
        self.assertIn('may already have been permanently deleted', str(raised.exception))
        self.assertIn('check the trash', str(raised.exception))
        run.assert_called_once()

    @unittest.skipUnless(os.name == 'posix', 'fake executable requires POSIX')
    def test_non_utf8_stderr_preserves_partial_deletion_warning(self):
        # This is an isolated fake, not the real gio command or desktop trash.
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / 'gio'
            fake.write_text("#!/bin/sh\n[ \"$1\" = trash ] && [ \"$2\" = --empty ] || exit 2\nprintf '\\377' >&2\nexit 1\n")
            fake.chmod(0o700)
            with patch.dict(os.environ, {'PATH': directory}):
                with self.assertRaisesRegex(RuntimeError, 'may already have been permanently deleted') as raised:
                    actions.empty_trash()
            self.assertIsInstance(raised.exception.__cause__, subprocess.CalledProcessError)

    def test_success_does_not_raise(self):
        with patch('avelin.actions.shutil.which', return_value='/usr/bin/gio'), \
             patch('avelin.actions.subprocess.run') as run:
            self.assertIsNone(actions.empty_trash())
            run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
