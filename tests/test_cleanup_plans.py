import unittest
from unittest.mock import patch

from avelin.cleanup_plans import Presence, ToolEvidence, build_cleanup_plan


class CleanupPlanTests(unittest.TestCase):
    def test_families_and_explicit_id_priority(self):
        for release, family, tool, package in [
            ({'ID': 'ubuntu', 'ID_LIKE': 'debian'}, 'debian', 'apt-get', 'apt'),
            ({'ID': 'debian'}, 'debian', 'apt-get', 'apt'),
            ({'ID': 'arch'}, 'arch', 'paccache', 'pacman-contrib'),
            ({'ID': 'fedora'}, 'dnf', 'dnf', 'dnf'),
            ({'ID': 'ubuntu', 'ID_LIKE': 'arch'}, 'debian', 'apt-get', 'apt'),
        ]:
            with self.subTest(release=release):
                result = build_cleanup_plan(release)
                self.assertEqual((result.family, result.matched_by), (family, 'ID'))
                self.assertEqual((result.options[0].executable_name, result.options[0].package_name), (tool, package))

    def test_like_is_ordered_and_labeled_as_inference(self):
        result = build_cleanup_plan({'ID': 'derivative', 'ID_LIKE': 'rhel fedora debian'})
        self.assertEqual((result.family, result.matched_by), ('dnf', 'ID_LIKE'))
        self.assertTrue(any('compatibility' in notice for notice in result.notices))

    def test_unknown_and_malformed_distro_do_not_guess(self):
        for release in (None, {}, {'ID': 'suse'}, {'ID': 'archlinux'},
                        {'ID': 'Arch', 'ID_LIKE': 'arch'},
                        {'ID': 'custom', 'ID_LIKE': 'debian;evil'},
                        {'ID': None, 'ID_LIKE': 'debian'}):
            with self.subTest(release=release):
                result = build_cleanup_plan(release)
                self.assertIsNone(result.family)
                self.assertEqual(result.options, ())

    def test_evidence_does_not_conflate_package_and_executable(self):
        for package, executable, availability in [
            (Presence.PRESENT, Presence.PRESENT, Presence.PRESENT),
            (Presence.ABSENT, Presence.ABSENT, Presence.ABSENT),
            (Presence.PRESENT, Presence.ABSENT, Presence.UNKNOWN),
            (Presence.ABSENT, Presence.PRESENT, Presence.UNKNOWN),
            (Presence.UNKNOWN, Presence.PRESENT, Presence.UNKNOWN),
            (Presence.ABSENT, Presence.UNKNOWN, Presence.UNKNOWN),
        ]:
            with self.subTest(package=package, executable=executable):
                plan = build_cleanup_plan({'ID': 'arch'}, {'paccache': ToolEvidence(package, executable)})
                option = plan.options[0]
                self.assertEqual((option.package_presence, option.executable_presence, option.availability),
                                 (package, executable, availability))
        self.assertEqual(build_cleanup_plan({'ID': 'arch'}).options[0].availability, Presence.UNKNOWN)
        with self.assertRaises(ValueError):
            ToolEvidence('present', Presence.PRESENT)
        with self.assertRaises(ValueError):
            build_cleanup_plan({'ID': 'arch'}, {'paccache': None})

    def test_safety_fields_remain_unknown_and_unapproved(self):
        for family in ('ubuntu', 'arch', 'fedora'):
            option = build_cleanup_plan({'ID': family}).options[0]
            self.assertIsNone(option.reclaimable_bytes)
            self.assertTrue(option.approval_required)
            self.assertFalse(option.approval_obtained)
            self.assertIn('not automatically reversible', option.reversibility)
            self.assertTrue(option.scope and option.risks and option.preview_limitations and option.source_urls)
        self.assertIn('root', build_cleanup_plan({'ID': 'fedora'}).options[0].scope)
        self.assertIn('uninstalled', ' '.join(build_cleanup_plan({'ID': 'arch'}).options[0].risks))

    def test_no_external_operations_even_with_present_tools(self):
        # Patch shared process, filesystem and network entry points: all calls must fail closed.
        with patch('subprocess.run', side_effect=AssertionError('process')), \
             patch('subprocess.Popen', side_effect=AssertionError('process')), \
             patch('os.system', side_effect=AssertionError('shell')), \
             patch('shutil.which', side_effect=AssertionError('probe')), \
             patch('builtins.open', side_effect=AssertionError('file')), \
             patch('os.remove', side_effect=AssertionError('delete')), \
             patch('os.unlink', side_effect=AssertionError('delete')):
            for distro, tool in [('ubuntu', 'apt-get'), ('arch', 'paccache'), ('fedora', 'dnf')]:
                plan = build_cleanup_plan({'ID': distro}, {tool: ToolEvidence(Presence.PRESENT, Presence.PRESENT)})
                self.assertFalse(plan.options[0].approval_obtained)


if __name__ == '__main__':
    unittest.main()
