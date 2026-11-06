import unittest
from unittest.mock import patch

from avelin.update_guidance import Guidance, InstallOrigin, update_guidance


class UpdateGuidanceTests(unittest.TestCase):
    def test_empty_unknown_and_invalid_evidence_fail_closed(self):
        for evidence in ((), (InstallOrigin.UNKNOWN,), ('flatpak',), (None,), None, ([1],)):
            with self.subTest(evidence=evidence):
                self.assertEqual(update_guidance(evidence).origin, InstallOrigin.UNKNOWN)

    def test_distinct_supported_origins(self):
        for origin, needle in ((InstallOrigin.PACKAGE, 'package-managed'),
                               (InstallOrigin.FLATPAK, 'Flatpak'),
                               (InstallOrigin.SOURCE, 'source checkout')):
            with self.subTest(origin=origin):
                result = update_guidance((origin,))
                self.assertIsInstance(result, Guidance)
                self.assertEqual(result.origin, origin)
                self.assertIn(needle, result.message)

    def test_conflicting_and_unknown_evidence_fail_closed(self):
        for evidence in ((InstallOrigin.FLATPAK, InstallOrigin.PACKAGE),
                         (InstallOrigin.SOURCE, InstallOrigin.UNKNOWN),
                         (InstallOrigin.FLATPAK, 'flatpak')):
            with self.subTest(evidence=evidence):
                self.assertEqual(update_guidance(evidence).origin, InstallOrigin.UNKNOWN)

    def test_duplicate_matching_evidence_is_not_conflict(self):
        self.assertEqual(update_guidance((InstallOrigin.SOURCE, InstallOrigin.SOURCE)).origin,
                         InstallOrigin.SOURCE)

    def test_rejects_mapping_and_bounded_input(self):
        self.assertEqual(update_guidance({InstallOrigin.PACKAGE: False}).origin, InstallOrigin.UNKNOWN)
        self.assertEqual(update_guidance([InstallOrigin.PACKAGE] * 64).origin, InstallOrigin.PACKAGE)
        self.assertEqual(update_guidance([InstallOrigin.PACKAGE] * 65).origin, InstallOrigin.UNKNOWN)

    def test_generator_is_rejected_without_consumption(self):
        def bad():
            raise AssertionError('must not consume')
            yield InstallOrigin.PACKAGE
        self.assertEqual(update_guidance(bad()).origin, InstallOrigin.UNKNOWN)

    def test_hash_bomb_rejected_before_hashing(self):
        class HashBomb:
            def __hash__(self):
                raise AssertionError('must not hash non-enum')
        for evidence in ((HashBomb(),), [InstallOrigin.PACKAGE, HashBomb()]):
            self.assertEqual(update_guidance(evidence).origin, InstallOrigin.UNKNOWN)

    def test_list_subclass_rejected_without_iteration(self):
        class HostileList(list):
            def __iter__(self):
                raise AssertionError('must not iterate subclass')
        self.assertEqual(update_guidance(HostileList([InstallOrigin.PACKAGE])).origin,
                         InstallOrigin.UNKNOWN)

    def test_no_host_inspection_or_execution(self):
        with patch('subprocess.run', side_effect=AssertionError('process executed')), \
             patch('subprocess.Popen', side_effect=AssertionError('process executed')), \
             patch('urllib.request.urlopen', side_effect=AssertionError('network used')), \
             patch('builtins.open', side_effect=AssertionError('file opened')):
            for origin in InstallOrigin:
                update_guidance((origin,))
            update_guidance()

    def test_unknown_never_claims_current_or_verified(self):
        message = update_guidance().message
        self.assertIn('unknown', message.lower())
        self.assertIn('Do not assume', message)


if __name__ == '__main__':
    unittest.main()
