"""Power-profile safety tests; no system commands or daemon calls are made."""
import subprocess
import unittest
from unittest.mock import patch

from avelin import actions


class PowerProfileSafetyTests(unittest.TestCase):
    def test_current_profile_is_read_only_noop(self):
        with patch('avelin.actions.power_profiles', return_value=(['balanced', 'performance'], 'balanced')), \
             patch('avelin.actions.subprocess.run') as run:
            self.assertIsNone(actions.set_power_profile('balanced'))
            run.assert_not_called()

    def test_other_available_profiles_are_blocked_without_writes(self):
        for profile in ('performance', 'power-saver'):
            with self.subTest(profile=profile), \
                 patch('avelin.actions.power_profiles', return_value=(['balanced', profile], 'balanced')), \
                 patch('avelin.actions.subprocess.run') as run:
                with self.assertRaisesRegex(RuntimeError, 'profile hold') as raised:
                    actions.set_power_profile(profile)
                self.assertIn('cannot restore', str(raised.exception))
                run.assert_not_called()

    def test_unknown_current_or_unavailable_profile_is_not_written(self):
        for state in (([], None), (['balanced'], None), (['balanced'], 'balanced')):
            with self.subTest(state=state), \
                 patch('avelin.actions.power_profiles', return_value=state), \
                 patch('avelin.actions.subprocess.run') as run:
                with self.assertRaises(RuntimeError):
                    actions.set_power_profile('performance')
                run.assert_not_called()

    def test_non_allowlisted_profile_is_rejected_before_discovery(self):
        with patch('avelin.actions.power_profiles') as discover:
            with self.assertRaises(ValueError):
                actions.set_power_profile('performance; whoami')
            discover.assert_not_called()


class PowerProfileDiscoverySafetyTests(unittest.TestCase):
    """Exercise discovery and mutation together with simulated subprocesses."""

    @staticmethod
    def result(output):
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=output)

    def test_missing_command_never_runs_or_sets(self):
        with patch('avelin.actions.shutil.which', return_value=None), \
             patch('avelin.actions.subprocess.run') as run:
            with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                actions.set_power_profile('performance')
            run.assert_not_called()

    def test_list_and_get_errors_fail_closed_without_set(self):
        failures = (
            OSError('cannot launch'),
            subprocess.TimeoutExpired(['powerprofilesctl'], 5),
            subprocess.CalledProcessError(1, ['powerprofilesctl']),
        )
        for stage in ('list', 'get'):
            for failure in failures:
                with self.subTest(stage=stage, failure=type(failure).__name__):
                    responses = [failure] if stage == 'list' else [
                        self.result('* balanced:\n  performance:\n'), failure
                    ]
                    with patch('avelin.actions.shutil.which', return_value='/usr/bin/powerprofilesctl'), \
                         patch('avelin.actions.subprocess.run', side_effect=responses) as run:
                        with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                            actions.set_power_profile('performance')
                    commands = [call.args[0] for call in run.call_args_list]
                    expected = [['powerprofilesctl', 'list']]
                    if stage == 'get':
                        expected.append(['powerprofilesctl', 'get'])
                    self.assertEqual(commands, expected)

    def test_malformed_or_inconsistent_discovery_never_sets(self):
        cases = (
            ('garbage\n', 'balanced\n'),
            ('* balanced:\n  performance:\n', 'unknown\n'),
            ('* balanced:\n', 'performance\n'),
            ('', ''),
        )
        for listing, current in cases:
            with self.subTest(listing=listing, current=current), \
                 patch('avelin.actions.shutil.which', return_value='/usr/bin/powerprofilesctl'), \
                 patch('avelin.actions.subprocess.run', side_effect=[self.result(listing), self.result(current)]) as run:
                with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                    actions.set_power_profile('performance')
                self.assertEqual([call.args[0] for call in run.call_args_list], [
                    ['powerprofilesctl', 'list'], ['powerprofilesctl', 'get']
                ])

    def test_observed_profile_change_between_list_and_get_does_not_write(self):
        # The list marks balanced active; get observes a later external change.
        for desired, should_raise in (('performance', False), ('balanced', True)):
            with self.subTest(desired=desired), \
                 patch('avelin.actions.shutil.which', return_value='/usr/bin/powerprofilesctl'), \
                 patch('avelin.actions.subprocess.run', side_effect=[
                     self.result('* balanced:\n  performance:\n'), self.result('performance\n')
                 ]) as run:
                if should_raise:
                    with self.assertRaisesRegex(RuntimeError, 'temporarily disabled'):
                        actions.set_power_profile(desired)
                else:
                    self.assertIsNone(actions.set_power_profile(desired))
                self.assertEqual([call.args[0] for call in run.call_args_list], [
                    ['powerprofilesctl', 'list'], ['powerprofilesctl', 'get']
                ])

    def test_external_change_after_get_does_not_make_avelin_write(self):
        # get returns balanced, then the simulated external actor selects performance.
        # The no-op is based on a stale snapshot; it does not verify final state.
        state = {'profile': 'balanced'}
        def run_read_only(command, **kwargs):
            if command == ['powerprofilesctl', 'list']:
                return self.result('* balanced:\n  performance:\n')
            if command == ['powerprofilesctl', 'get']:
                observed = state['profile']
                state['profile'] = 'performance'
                return self.result(observed + '\n')
            self.fail(f'unexpected command: {command!r}')

        with patch('avelin.actions.shutil.which', return_value='/usr/bin/powerprofilesctl'), \
             patch('avelin.actions.subprocess.run', side_effect=run_read_only) as run:
            self.assertIsNone(actions.set_power_profile('balanced'))
        self.assertEqual(state['profile'], 'performance')
        self.assertEqual([call.args[0] for call in run.call_args_list], [
            ['powerprofilesctl', 'list'], ['powerprofilesctl', 'get']
        ])


if __name__ == '__main__':
    unittest.main()
