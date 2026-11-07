import unittest

from avelin.optimize.preview import preview
from avelin.optimize.registry import RegistryError
from test_registry import entry


def observation(distro=None, desktop='gnome', hardware=None):
    return {'distro': distro, 'desktop': desktop, 'hardware': hardware}


def capability(supported=True, readable=True, writable=True, current=True):
    return {'supported': supported, 'readable': readable, 'writable': writable, 'current': current}


class PreviewTests(unittest.TestCase):
    def test_ready_contains_reviewable_exact_values(self):
        result = preview(entry(), observation(), capability())
        self.assertEqual('ready', result['status'])
        self.assertEqual('org.gnome.desktop.interface', result['schema'])
        self.assertEqual('enable-animations', result['key'])
        self.assertIs(result['current'], True)
        self.assertIs(result['target'], False)
        self.assertEqual(entry()['source'], result['source'])
        self.assertEqual('low', result['risk'])
        self.assertFalse(result['advanced'])
        self.assertTrue(result['reversible'])

    def test_same_input_same_result(self):
        self.assertEqual(preview(entry(), observation(), capability()),
                         preview(entry(), observation(), capability()))

    def test_already_target_needs_no_write(self):
        self.assertEqual('no_change', preview(entry(), observation(), capability(writable=False, current=False))['status'])

    def test_unavailable_and_unknown_are_distinct(self):
        cases = [(capability(supported=False, readable=None, writable=None, current=None), 'unavailable'),
                 (capability(readable=False, writable=False, current=None), 'unavailable'),
                 (capability(writable=False), 'unavailable'),
                 (capability(supported=None, readable=None, writable=None, current=None), 'unknown'),
                 (capability(writable=None), 'unknown'),
                 (capability(current=None), 'unknown')]
        for state, expected in cases:
            with self.subTest(state=state):
                self.assertEqual(expected, preview(entry(), observation(), state)['status'])

    def test_inapplicable_and_unknown_applicability(self):
        self.assertEqual('not_applicable', preview(entry(), observation(desktop='kde'), capability())['status'])
        self.assertEqual('unknown', preview(entry(), observation(desktop=None), capability())['status'])

    def test_reject_malformed_and_inconsistent_capability(self):
        cases = [None, {}, {'supported': True}, capability(supported=1),
                 capability(current=1), capability(supported=False),
                 capability(readable=False), {**capability(), 'extra': True}]
        for state in cases:
            with self.subTest(state=state), self.assertRaises(RegistryError):
                preview(entry(), observation(), state)

    def test_bad_entry_rejected_even_if_inapplicable(self):
        item = entry(); item['apply']['value'] = 'false'
        with self.assertRaises(RegistryError):
            preview(item, observation(desktop='kde'), capability())


if __name__ == '__main__':
    unittest.main()
