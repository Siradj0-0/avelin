import unittest

from avelin.optimize.applicability import evaluate_applicability
from avelin.optimize.registry import RegistryError


def rules(distros=(), desktops=(), hardware=()):
    return {'distros': list(distros), 'desktops': list(desktops), 'hardware': list(hardware)}


def observed(distro=None, desktop=None, hardware=None):
    return {'distro': distro, 'desktop': desktop, 'hardware': hardware}


class ApplicabilityTests(unittest.TestCase):
    def test_unrestricted_ignores_unknowns(self):
        self.assertEqual('applicable', evaluate_applicability(rules(), observed()))

    def test_all_dimensions_match(self):
        spec = rules(['ubuntu', 'debian'], ['gnome'], ['amd-gpu', 'intel-gpu'])
        self.assertEqual('applicable', evaluate_applicability(spec, observed('ubuntu', 'gnome', ['intel-gpu', 'ssd'])))

    def test_unknown_is_not_a_match(self):
        for spec, obs in [(rules(['ubuntu']), observed()),
                          (rules(desktops=['gnome']), observed()),
                          (rules(hardware=['ssd']), observed())]:
            with self.subTest(spec=spec):
                self.assertEqual('unknown', evaluate_applicability(spec, obs))

    def test_known_mismatch_wins_over_unknown(self):
        spec = rules(['ubuntu'], ['gnome'], ['ssd'])
        self.assertEqual('not_applicable', evaluate_applicability(spec, observed('fedora', None, None)))
        self.assertEqual('not_applicable', evaluate_applicability(spec, observed(None, None, [])))
        self.assertEqual('unknown', evaluate_applicability(spec, observed('ubuntu', 'gnome', None)))

    def test_hardware_empty_is_known_absence(self):
        self.assertEqual('not_applicable', evaluate_applicability(rules(hardware=['ssd']), observed(hardware=[])))
        self.assertEqual('unknown', evaluate_applicability(rules(hardware=['ssd']), observed(hardware=None)))

    def test_observations_and_rules_must_be_valid(self):
        for value in (None, {}, {'distro': 'ubuntu', 'desktop': None},
                      observed('Ubuntu Desktop'), observed(hardware='ssd'),
                      observed(hardware=['ssd', 'ssd']), observed(hardware=['x'] * 101),
                      observed(desktop=0)):
            with self.subTest(value=value), self.assertRaises(RegistryError):
                evaluate_applicability(rules(), value)
        with self.assertRaises(RegistryError):
            evaluate_applicability({'distros': 'ubuntu', 'desktops': [], 'hardware': []}, observed())


if __name__ == '__main__':
    unittest.main()
