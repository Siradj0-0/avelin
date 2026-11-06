import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from avelin.cleanup_plans import DnfImplementation, Presence, ToolEvidence, build_cleanup_plan


class CleanupPlanTests(unittest.TestCase):
    def test_families_and_explicit_id_priority(self):
        for release, family, tool, package in [
            ({'ID': 'ubuntu', 'ID_LIKE': 'debian'}, 'debian', 'apt-get', 'apt'),
            ({'ID': 'debian'}, 'debian', 'apt-get', 'apt'),
            ({'ID': 'arch'}, 'arch', 'paccache', 'pacman-contrib'),
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

    def test_known_id_does_not_use_malformed_like(self):
        result = build_cleanup_plan({'ID': 'ubuntu', 'ID_LIKE': 'arch;evil'})
        self.assertEqual((result.family, result.matched_by), ('debian', 'ID'))
        self.assertEqual(result.options[0].id, 'apt-autoclean')

    def test_dnf_requires_separate_legacy_evidence(self):
        distro = {'ID': 'fedora'}
        for implementation in (DnfImplementation.UNKNOWN, DnfImplementation.DNF5):
            for package, executable in ((Presence.PRESENT, Presence.PRESENT),
                                        (Presence.UNKNOWN, Presence.UNKNOWN)):
                result = build_cleanup_plan(distro, {'dnf': ToolEvidence(package, executable, implementation)})
                self.assertEqual(result.family, 'dnf')
                self.assertEqual(result.options, ())
                self.assertTrue(any('No DNF option' in text for text in result.notices))
        self.assertEqual(build_cleanup_plan(distro).options, ())
        result = build_cleanup_plan(distro, {'dnf': ToolEvidence(Presence.UNKNOWN, Presence.PRESENT, DnfImplementation.LEGACY)})
        self.assertEqual(result.options[0].package_name, 'dnf')
        self.assertEqual(result.options[0].availability, Presence.UNKNOWN)
        self.assertIn('caller-supplied', result.notices[-1])
        with self.assertRaises(ValueError):
            ToolEvidence(dnf_implementation='legacy-dnf')

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
        dnf_evidence = {'dnf': ToolEvidence(dnf_implementation=DnfImplementation.LEGACY)}
        for family in ('ubuntu', 'arch', 'fedora'):
            option = build_cleanup_plan({'ID': family}, dnf_evidence).options[0]
            self.assertIsNone(option.reclaimable_bytes)
            self.assertTrue(option.approval_required)
            self.assertFalse(option.approval_obtained)
            self.assertIn('not automatically reversible', option.reversibility)
            self.assertTrue(option.scope and option.risks and option.preview_limitations and option.source_urls)
        self.assertIn('root', build_cleanup_plan({'ID': 'fedora'}, dnf_evidence).options[0].scope)
        self.assertIn('uninstalled', ' '.join(build_cleanup_plan({'ID': 'arch'}).options[0].risks))

    def test_module_body_and_plans_with_guarded_entry_points(self):
        # Read/compile before guards; execute a fresh module body and build plans
        # while representative I/O entry points raise. This is not an exhaustive
        # proof that all possible I/O mechanisms are intercepted.
        source = Path(__file__).resolve().parents[1] / 'avelin' / 'cleanup_plans.py'
        code = compile(source.read_text(), str(source), 'exec')
        module = types.ModuleType('_cleanup_plans_guarded')
        sys.modules[module.__name__] = module
        try:
            with patch('subprocess.run', side_effect=AssertionError('process')), \
                 patch('subprocess.Popen', side_effect=AssertionError('process')), \
                 patch('os.system', side_effect=AssertionError('shell')), \
                 patch('shutil.which', side_effect=AssertionError('probe')), \
                 patch('builtins.open', side_effect=AssertionError('file')), \
                 patch('os.open', side_effect=AssertionError('file')), \
                 patch('os.scandir', side_effect=AssertionError('directory scan')), \
                 patch('os.listdir', side_effect=AssertionError('directory list')), \
                 patch('os.remove', side_effect=AssertionError('delete')), \
                 patch('os.unlink', side_effect=AssertionError('delete')), \
                 patch('socket.socket', side_effect=AssertionError('network')), \
                 patch('socket.create_connection', side_effect=AssertionError('network')), \
                 patch('urllib.request.urlopen', side_effect=AssertionError('network')):
                exec(code, module.__dict__)
                for distro, tool in [('ubuntu', 'apt-get'), ('arch', 'paccache'), ('fedora', 'dnf')]:
                    implementation = (module.DnfImplementation.LEGACY if tool == 'dnf'
                                      else module.DnfImplementation.UNKNOWN)
                    evidence = module.ToolEvidence(module.Presence.PRESENT, module.Presence.PRESENT, implementation)
                    plan = module.build_cleanup_plan({'ID': distro}, {tool: evidence})
                    self.assertFalse(plan.options[0].approval_obtained)
        finally:
            del sys.modules[module.__name__]


if __name__ == '__main__':
    unittest.main()
