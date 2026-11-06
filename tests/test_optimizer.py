import os
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

from avelin import optimizer as opt


class Variant:
    def __init__(self, value):
        self.value = value

    def unpack(self):
        return self.value


class Settings:
    def __init__(self, default=True, user=None):
        self.default = default
        self.user = user
        self.writable = True
        self.reject = False
        self.writes = []

    def is_writable(self, key):
        return self.writable

    def get_boolean(self, key):
        return self.default if self.user is None else self.user

    def get_user_value(self, key):
        return None if self.user is None else Variant(self.user)

    def set_boolean(self, key, value):
        self.writes.append(('set', key, value))
        if self.reject:
            return False
        self.user = value
        return True

    def reset(self, key):
        self.writes.append(('reset', key))
        self.user = None


class AnimationTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings()
        self.patcher = patch.object(opt, '_gnome_settings', return_value=self.settings)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_default_restores_unset_user_value(self):
        snapshot = opt.prepare(opt.ANIMATIONS)
        self.assertEqual((snapshot.previous, snapshot.user_value), (True, None))
        self.assertEqual(self.settings.writes, [])
        opt.apply(snapshot)
        self.assertIs(self.settings.user, False)
        opt.restore(snapshot)
        self.assertIsNone(self.settings.user)
        self.assertEqual(self.settings.writes, [('set', 'enable-animations', False), ('reset', 'enable-animations')])

    def test_explicit_value_restored(self):
        self.settings.user = True
        snapshot = opt.prepare(opt.ANIMATIONS)
        opt.apply(snapshot)
        opt.restore(snapshot)
        self.assertIs(self.settings.user, True)
        self.assertEqual(self.settings.writes[-1], ('set', 'enable-animations', True))

    def test_already_disabled_is_noop(self):
        self.settings.user = False
        snapshot = opt.prepare(opt.ANIMATIONS)
        self.assertFalse(snapshot.changed)
        opt.apply(snapshot)
        opt.restore(snapshot)
        self.assertEqual(self.settings.writes, [])

    def test_stale_snapshot_and_external_edit_are_not_overwritten(self):
        snapshot = opt.prepare(opt.ANIMATIONS)
        self.settings.user = True  # same effective value, different user override
        with self.assertRaises(opt.Conflict):
            opt.apply(snapshot)
        self.assertEqual(self.settings.writes, [])
        self.settings.user = None
        opt.apply(snapshot)
        self.settings.user = True
        with self.assertRaises(opt.Conflict):
            opt.restore(snapshot)
        self.assertIs(self.settings.user, True)

    def test_default_change_after_apply_restores_unset_not_old_default(self):
        snapshot = opt.prepare(opt.ANIMATIONS)
        opt.apply(snapshot)
        self.settings.default = False
        opt.restore(snapshot)
        self.assertIsNone(self.settings.user)
        self.assertFalse(self.settings.get_boolean('enable-animations'))

    def test_rejected_write(self):
        snapshot = opt.prepare(opt.ANIMATIONS)
        self.settings.reject = True
        with self.assertRaises(opt.Unavailable):
            opt.apply(snapshot)
        self.assertIsNone(self.settings.user)

    def test_write_can_succeed_before_error_snapshot_is_usable(self):
        snapshot = opt.prepare(opt.ANIMATIONS)
        def partial(key, value):
            self.settings.user = value
            raise RuntimeError('transport failed')
        with patch.object(self.settings, 'set_boolean', side_effect=partial):
            with self.assertRaises(opt.Unavailable):
                opt.apply(snapshot)
        opt.restore(snapshot)
        self.assertIsNone(self.settings.user)


class DetectionTests(unittest.TestCase):
    def test_non_gnome_fails_closed(self):
        with patch.object(opt.sys, 'platform', 'linux'), patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'KDE'}):
            with self.assertRaises(opt.Unavailable):
                opt.prepare(opt.ANIMATIONS)

    def test_schema_key_type_and_writability_detected(self):
        fake = Settings()
        keytype = types.SimpleNamespace(dup_string=lambda: 'b')
        key = types.SimpleNamespace(get_value_type=lambda: keytype)
        schema = types.SimpleNamespace(has_key=lambda k: True, get_key=lambda k: key)
        source = types.SimpleNamespace(lookup=lambda name, recursive: schema)
        gio = types.SimpleNamespace(SettingsSchemaSource=types.SimpleNamespace(get_default=lambda: source), Settings=types.SimpleNamespace(new_full=lambda *args: fake))
        modules = {'gi': types.ModuleType('gi'), 'gi.repository': types.SimpleNamespace(Gio=gio)}
        with patch.dict(sys.modules, modules), patch.object(opt.sys, 'platform', 'linux'), patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'ubuntu:GNOME'}):
            self.assertTrue(opt.prepare(opt.ANIMATIONS).changed)
            fake.writable = False
            with self.assertRaises(opt.Unavailable):
                opt.prepare(opt.ANIMATIONS)
            fake.writable = True
            schema.has_key = lambda k: False
            with self.assertRaises(opt.Unavailable):
                opt.prepare(opt.ANIMATIONS)
            schema.has_key = lambda k: True
            keytype.dup_string = lambda: 's'
            with self.assertRaises(opt.Unavailable):
                opt.prepare(opt.ANIMATIONS)

    def test_missing_gi_and_missing_schema_are_unavailable(self):
        with patch.object(opt.sys, 'platform', 'linux'), patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'GNOME'}), patch.dict(sys.modules, {'gi': None}):
            with self.assertRaises(opt.Unavailable):
                opt.prepare(opt.ANIMATIONS)

    def test_unknown_ids_and_malformed_snapshots(self):
        with self.assertRaises(ValueError):
            opt.prepare('delete-everything')
        for snapshot in [opt.Snapshot('other', True), opt.Snapshot(opt.PERFORMANCE, 'evil'), opt.Snapshot(opt.ANIMATIONS, True, None, False), opt.Snapshot(opt.ANIMATIONS, 1)]:
            with self.assertRaises(ValueError):
                opt.apply(snapshot)
            with self.assertRaises(ValueError):
                opt.restore(snapshot)


class PowerTests(unittest.TestCase):
    def setUp(self):
        self.current = 'balanced'
        self.available = {'power-saver', 'balanced', 'performance'}
        self.calls = []
        self.patches = [patch.object(opt.sys, 'platform', 'linux'), patch.object(opt.shutil, 'which', return_value='/usr/bin/powerprofilesctl'), patch.object(opt.subprocess, 'run', side_effect=self.run_command)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def run_command(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if args[1] == 'list':
            text = '\n'.join(('  * ' if p == self.current else '    ') + p + ':\n    Driver: test' for p in sorted(self.available))
        elif args[1] == 'get':
            text = self.current + '\n'
        elif args[1] == 'set':
            self.current = args[2]
            text = ''
        else:
            self.fail('Unexpected command')
        return subprocess.CompletedProcess(args, 0, stdout=text)

    def test_round_trip_and_strict_command_shape(self):
        snapshot = opt.prepare(opt.PERFORMANCE)
        self.assertFalse(any(args[1] == 'set' for args, _ in self.calls))
        opt.apply(snapshot)
        self.assertEqual(self.current, 'performance')
        opt.restore(snapshot)
        self.assertEqual(self.current, 'balanced')
        for args, kwargs in self.calls:
            self.assertEqual(args[0], '/usr/bin/powerprofilesctl')
            self.assertIn(args[1:], [['list'], ['get'], ['set', 'performance'], ['set', 'balanced']])
            self.assertNotIn('shell', kwargs)
            self.assertEqual(kwargs['timeout'], 10)
            self.assertTrue(kwargs['check'])

    def test_unavailable_and_bad_output(self):
        self.available.remove('performance')
        with self.assertRaises(opt.Unavailable):
            opt.prepare(opt.PERFORMANCE)
        self.current = 'bogus'
        with self.assertRaises(opt.Unavailable):
            opt.prepare(opt.PERFORMANCE)

    def test_unadvertised_previous_refuses_restore(self):
        snapshot = opt.prepare(opt.PERFORMANCE)
        opt.apply(snapshot)
        self.available.remove('balanced')
        with self.assertRaises(opt.Unavailable):
            opt.restore(snapshot)
        self.assertEqual(self.current, 'performance')

    def test_stale_and_external_profile_refuse_overwrite(self):
        snapshot = opt.prepare(opt.PERFORMANCE)
        self.current = 'power-saver'
        with self.assertRaises(opt.Conflict):
            opt.apply(snapshot)
        self.current = 'balanced'
        opt.apply(snapshot)
        self.current = 'power-saver'
        with self.assertRaises(opt.Conflict):
            opt.restore(snapshot)
        self.assertEqual(self.current, 'power-saver')

    def test_already_performance_no_write(self):
        self.current = 'performance'
        snapshot = opt.prepare(opt.PERFORMANCE)
        opt.apply(snapshot)
        opt.restore(snapshot)
        self.assertFalse(any(args[1] == 'set' for args, _ in self.calls))

    def test_invalid_commands_and_timeouts(self):
        for command, profile in [('set', ';rm'), ('get', 'balanced'), ('launch', None), ('set', None)]:
            with self.assertRaises(ValueError):
                opt._power_command(command, profile)
        with patch.object(opt.subprocess, 'run', side_effect=subprocess.TimeoutExpired('powerprofilesctl', 10)):
            with self.assertRaises(opt.Unavailable):
                opt.prepare(opt.PERFORMANCE)

    def test_missing_binary_and_failed_service(self):
        with patch.object(opt.shutil, 'which', return_value=None):
            with self.assertRaises(opt.Unavailable):
                opt.prepare(opt.PERFORMANCE)
        with patch.object(opt.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'powerprofilesctl')):
            with self.assertRaises(opt.Unavailable):
                opt.prepare(opt.PERFORMANCE)

    def test_profile_disappears_before_apply(self):
        snapshot = opt.prepare(opt.PERFORMANCE)
        self.available.remove('performance')
        with self.assertRaises(opt.Unavailable):
            opt.apply(snapshot)
        self.assertFalse(any(args[1] == 'set' for args, _ in self.calls))

    def test_set_acknowledged_but_not_effective_is_error(self):
        snapshot = opt.prepare(opt.PERFORMANCE)
        original = self.run_command
        def no_effect(args, **kwargs):
            if args[1] == 'set':
                return subprocess.CompletedProcess(args, 0, stdout='')
            return original(args, **kwargs)
        with patch.object(opt.subprocess, 'run', side_effect=no_effect):
            with self.assertRaises(opt.Unavailable):
                opt.apply(snapshot)

    def test_verification_failure_does_not_destroy_snapshot(self):
        snapshot = opt.prepare(opt.PERFORMANCE)
        original = self.run_command
        def transient(args, **kwargs):
            result = original(args, **kwargs)
            if args[1] == 'set':
                raise subprocess.TimeoutExpired('powerprofilesctl', 10)
            return result
        with patch.object(opt.subprocess, 'run', side_effect=transient):
            with self.assertRaises(opt.Unavailable):
                opt.apply(snapshot)
        self.assertEqual(self.current, 'performance')
        opt.restore(snapshot)
        self.assertEqual(self.current, 'balanced')


if __name__ == '__main__':
    unittest.main()
