import copy
import unittest

from avelin.optimize.registry import RegistryError, validate_catalog


def entry():
    return {
        'id': 'gnome.animations',
        'description': 'Disable interface animations.',
        'source': 'https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/main/schemas/org.gnome.desktop.interface.gschema.xml.in',
        'risk': 'low',
        'advanced': False,
        'reversible': True,
        'warning': '',
        'read': {'type': 'gsettings_boolean', 'schema': 'org.gnome.desktop.interface', 'key': 'enable-animations'},
        'apply': {'type': 'gsettings_boolean', 'value': False},
        'revert': {'type': 'snapshot'},
        'applicability': {'distros': [], 'desktops': ['gnome'], 'hardware': []},
    }


class RegistryTests(unittest.TestCase):
    def test_valid_catalog(self):
        validate_catalog({'version': 1, 'entries': [entry()]})

    def test_root_and_entry_must_be_strict(self):
        invalid = [None, [], {}, {'version': True, 'entries': []},
                   {'version': 2, 'entries': []}, {'version': 1, 'entries': [], 'extra': 1},
                   {'version': 1, 'entries': [None]}]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(RegistryError):
                validate_catalog(value)
        for mutation in ({'extra': 1}, {'description': ''}, {'id': 'BAD ID'},
                         {'source': 'http://example.com'}, {'source': 'https://user@example.com'},
                         {'source': 'https://example.com/bad path'}, {'risk': 'unknown'},
                         {'advanced': 1}, {'reversible': 1}):
            item = entry(); item.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(RegistryError):
                validate_catalog({'version': 1, 'entries': [item]})

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(RegistryError):
            validate_catalog({'version': 1, 'entries': [entry(), entry()]})

    def test_cannot_encode_commands_or_arbitrary_keys(self):
        for field, value in [('read', {'type': 'shell', 'command': 'id'}),
                             ('read', {'type': 'gsettings_boolean', 'schema': 'org.gnome.desktop.interface', 'key': 'enable-animations', 'command': 'id'}),
                             ('apply', {'type': 'shell', 'command': 'id'}),
                             ('apply', {'type': 'gsettings_boolean', 'value': 'false'}),
                             ('revert', {'type': 'snapshot', 'command': 'id'})]:
            item = entry(); item[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(RegistryError):
                validate_catalog({'version': 1, 'entries': [item]})

    def test_reversibility_and_advanced_gates(self):
        cases = [dict(reversible=True, revert=None),
                 dict(reversible=False, revert=None, warning=''),
                 dict(reversible=False, revert={'type': 'snapshot'}, warning='Irreversible'),
                 dict(risk='high', advanced=False)]
        for changes in cases:
            item = entry(); item.update(changes)
            with self.subTest(changes=changes), self.assertRaises(RegistryError):
                validate_catalog({'version': 1, 'entries': [item]})
        item = entry(); item.update(reversible=False, revert=None, warning='Cannot restore previous state.')
        validate_catalog({'version': 1, 'entries': [item]})

    def test_applicability_is_explicit_and_bounded(self):
        for value in ({}, {'distros': [], 'desktops': [], 'hardware': [], 'extra': []},
                      {'distros': 'ubuntu', 'desktops': [], 'hardware': []},
                      {'distros': ['Ubuntu Desktop'], 'desktops': [], 'hardware': []},
                      {'distros': ['ubuntu', 'ubuntu'], 'desktops': [], 'hardware': []},
                      {'distros': ['x'] * 101, 'desktops': [], 'hardware': []}):
            item = entry(); item['applicability'] = value
            with self.subTest(value=value), self.assertRaises(RegistryError):
                validate_catalog({'version': 1, 'entries': [item]})

    def test_validation_does_not_mutate_input(self):
        value = {'version': 1, 'entries': [entry()]}; before = copy.deepcopy(value)
        validate_catalog(value)
        self.assertEqual(before, value)

class ParsingTests(unittest.TestCase):
    def test_parse_and_reject_duplicate_keys(self):
        import json
        from avelin.optimize.registry import parse_catalog
        catalog = {'version': 1, 'entries': [entry()]}
        self.assertEqual(catalog, parse_catalog(json.dumps(catalog)))
        for text in ('{"version":1,"version":1,"entries":[]}', '{', ' ' * (1024 * 1024 + 1)):
            with self.subTest(text=text[:30]), self.assertRaises(RegistryError):
                parse_catalog(text)

    def test_bundled_catalog_is_valid(self):
        from pathlib import Path
        from avelin.optimize.registry import parse_catalog
        data = Path(__file__).resolve().parents[1] / 'catalog.json'
        catalog = parse_catalog(data.read_text(encoding='utf-8'))
        self.assertEqual(['gnome.animations'], [item['id'] for item in catalog['entries']])


if __name__ == '__main__':
    unittest.main()
