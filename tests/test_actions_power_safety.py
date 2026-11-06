"""Power-profile safety tests; no system commands or daemon calls are made."""
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


if __name__ == '__main__':
    unittest.main()
