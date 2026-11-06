import dataclasses
import unittest

from avelin.optimize.registry import RegistryError
from avelin.optimize.snapshot import capture_snapshot
from test_registry import entry


def obs(effective=True, override_present=False, override_value=None):
    return {'effective': effective, 'override_present': override_present, 'override_value': override_value}


class SnapshotTests(unittest.TestCase):
    def test_absent_override_is_not_false_override(self):
        absent = capture_snapshot(entry(), obs(effective=False))
        explicit = capture_snapshot(entry(), obs(effective=False, override_present=True, override_value=False))
        self.assertEqual((False, False, None), (absent.effective, absent.override_present, absent.override_value))
        self.assertEqual((False, True, False), (explicit.effective, explicit.override_present, explicit.override_value))
        self.assertNotEqual(absent, explicit)

    def test_explicit_true_override_and_identity_are_preserved(self):
        snap = capture_snapshot(entry(), obs(True, True, True))
        self.assertEqual(('gnome.animations', 'org.gnome.desktop.interface', 'enable-animations'),
                         (snap.setting_id, snap.schema, snap.key))
        self.assertIs(snap.effective, True)
        self.assertIs(snap.override_value, True)
        self.assertIs(snap.target, False)

    def test_snapshot_is_immutable_and_independent_of_input(self):
        data = entry(); values = obs(True, True, True)
        snap = capture_snapshot(data, values)
        data['read']['key'] = 'something-else'; values['override_value'] = False
        self.assertEqual('enable-animations', snap.key)
        self.assertTrue(snap.override_value)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            snap.effective = False

    def test_rejects_unknown_and_inconsistent_observations(self):
        invalid = [None, {}, obs(effective=None), obs(override_present=None),
                   obs(override_present=True, override_value=None),
                   obs(override_present=False, override_value=False),
                   obs(effective=1), obs(override_present=1), obs(True, True, 1),
                   obs(effective=True, override_present=True, override_value=False),
                   {**obs(), 'extra': True}]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(RegistryError):
                capture_snapshot(entry(), value)

    def test_invalid_or_irreversible_record_cannot_be_captured(self):
        value = entry(); value.update(reversible=False, revert=None, warning='Irreversible')
        with self.assertRaises(RegistryError):
            capture_snapshot(value, obs())
        value = entry(); value['read']['key'] = 'bad key'
        with self.assertRaises(RegistryError):
            capture_snapshot(value, obs())


if __name__ == '__main__':
    unittest.main()
