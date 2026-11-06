import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from avelin import undo_journal as uj


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'journal'
        self.path.mkdir(mode=0o700)
        self.journal = uj.Journal(self.path)

    def seed(self, setting='gnome-animations', previous=True, user=None):
        with self.journal.locked() as session:
            return session.prepare(setting, previous, user)

    def child(self, source):
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        return subprocess.run([sys.executable, '-c', source, str(self.path)], env=env,
                              capture_output=True, text=True, timeout=5)

    def write_raw(self, contents):
        file = self.path / 'undo.json'
        file.write_bytes(contents)
        file.chmod(0o600)

    def test_lifecycle_and_recovery_classification(self):
        with self.journal.locked() as s:
            self.assertIsNone(s.read())
            self.assertEqual(uj.recovery(None), 'empty')
            r = s.prepare('gnome-animations', True, None)
            tx = r['transaction']
            for state, expected in [('prepared', 'not-started'), ('applying', 'apply-uncertain'),
                                    ('verified', 'undo-needs-current-state-check'),
                                    ('restoring', 'restore-uncertain'), ('restored', 'complete')]:
                self.assertEqual(uj.recovery(s.read()), expected)
                if state != 'restored':
                    s.advance(tx, state, uj._NEXT[state])
            s.discard(tx)
            self.assertIsNone(s.read())
        self.assertEqual(stat.S_IMODE((self.path / 'undo.lock').stat().st_mode), 0o600)

    def test_explicit_override_and_power_snapshot_round_trip(self):
        for setting, previous, user in [('gnome-animations', True, True),
                                         ('power-performance', 'power-saver', None),
                                         ('power-performance', 'balanced', None)]:
            with self.subTest(setting=setting, previous=previous):
                with self.journal.locked() as s:
                    record = s.prepare(setting, previous, user)
                    self.assertEqual((s.read()['previous'], s.read()['user_value']), (previous, user))
                    self.assertEqual(stat.S_IMODE((self.path / 'undo.json').stat().st_mode), 0o600)
                    s.discard(record['transaction'])

    def test_prepare_does_not_overwrite_existing(self):
        r = self.seed()
        with self.journal.locked() as s:
            with self.assertRaises(uj.Conflict):
                s.prepare('power-performance', 'balanced')
            self.assertEqual(s.read(), r)

    def test_stale_token_state_and_disallowed_transitions(self):
        r = self.seed()
        with self.journal.locked() as s:
            for tx, a, b in [('0' * 32, 'prepared', 'applying'), (r['transaction'], 'prepared', 'verified'),
                             (r['transaction'], 'applying', 'verified'), (r['transaction'], 'prepared', 'restored'),
                             ('../bad', 'prepared', 'applying')]:
                with self.assertRaises(uj.Conflict):
                    s.advance(tx, a, b)
            s.advance(r['transaction'], 'prepared', 'applying')
            with self.assertRaises(uj.Conflict):
                s.discard(r['transaction'])
            self.assertEqual(s.read()['state'], 'applying')

    def test_cannot_discard_verified_or_restoring(self):
        r = self.seed()
        with self.journal.locked() as s:
            s.advance(r['transaction'], 'prepared', 'applying')
            s.advance(r['transaction'], 'applying', 'verified')
            with self.assertRaises(uj.Conflict):
                s.discard(r['transaction'])
            s.advance(r['transaction'], 'verified', 'restoring')
            with self.assertRaises(uj.Conflict):
                s.discard(r['transaction'])

    def test_session_closed(self):
        with self.journal.locked() as s:
            pass
        with self.assertRaises(uj.JournalError):
            s.read()

    def test_busy_lock_in_another_process(self):
        with self.journal.locked():
            result = self.child("import sys; from avelin.undo_journal import Journal, Busy\ntry:\n with Journal(sys.argv[1]).locked(): pass\nexcept Busy: sys.exit(23)\nsys.exit(1)")
            self.assertEqual(result.returncode, 23, result.stderr)
        with self.journal.locked() as s:
            self.assertIsNone(s.read())

    def test_crash_after_marking_applying_is_uncertain(self):
        code = "import sys,os; from avelin.undo_journal import Journal\nwith Journal(sys.argv[1]).locked() as s:\n r=s.prepare('gnome-animations',True); s.advance(r['transaction'],'prepared','applying'); os._exit(0)"
        result = self.child(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        with self.journal.locked() as s:
            self.assertEqual(uj.recovery(s.read()), 'apply-uncertain')
            with self.assertRaises(uj.Conflict):
                s.discard(s.read()['transaction'])

    def test_crash_after_marking_restoring_is_uncertain(self):
        code = "import sys,os; from avelin.undo_journal import Journal\nwith Journal(sys.argv[1]).locked() as s:\n r=s.prepare('power-performance','balanced'); t=r['transaction']; s.advance(t,'prepared','applying'); s.advance(t,'applying','verified'); s.advance(t,'verified','restoring'); os._exit(0)"
        self.assertEqual(self.child(code).returncode, 0)
        with self.journal.locked() as s:
            self.assertEqual(uj.recovery(s.read()), 'restore-uncertain')

    def test_manual_resolution_of_each_uncertain_outcome(self):
        outcomes = [('applying', 'not-applied', 'prepared'), ('applying', 'applied', 'verified'),
                    ('restoring', 'not-restored', 'verified'), ('restoring', 'restored', 'restored')]
        for initial, outcome, target in outcomes:
            with self.subTest(outcome=outcome):
                with tempfile.TemporaryDirectory() as directory:
                    with uj.Journal(directory).locked() as s:
                        r = s.prepare('gnome-animations', True)
                        tx = r['transaction']
                        s.advance(tx, 'prepared', 'applying')
                        if initial == 'restoring':
                            s.advance(tx, 'applying', 'verified')
                            s.advance(tx, 'verified', 'restoring')
                        with self.assertRaises(uj.Conflict):
                            s.resolve_uncertain('0' * 32, initial, outcome)
                        with self.assertRaises(uj.Conflict):
                            s.resolve_uncertain(tx, initial, 'guess')
                        self.assertEqual(s.resolve_uncertain(tx, initial, outcome)['state'], target)

    def test_symlink_swapped_during_persist_is_rejected(self):
        r = self.seed()
        victim = Path(self.tmp.name) / 'victim'
        victim.write_text('untouched')
        real_fsync = os.fsync
        swapped = False
        def swap(fd):
            nonlocal swapped
            real_fsync(fd)
            if not swapped and stat.S_ISREG(os.fstat(fd).st_mode):
                data = self.path / 'undo.json'
                data.unlink()
                data.symlink_to(victim)
                swapped = True
        with self.journal.locked() as s, patch('avelin.undo_journal.os.fsync', side_effect=swap):
            with self.assertRaises(OSError):
                s.advance(r['transaction'], 'prepared', 'applying')
        self.assertTrue(swapped)
        self.assertEqual(victim.read_text(), 'untouched')

    def test_rename_succeeds_then_reports_failure(self):
        r = self.seed()
        real_replace = os.replace
        def partial(*args, **kwargs):
            real_replace(*args, **kwargs)
            raise OSError('late error')
        with self.journal.locked() as s, patch('avelin.undo_journal.os.replace', side_effect=partial):
            with self.assertRaises(uj.DurabilityUncertain):
                s.advance(r['transaction'], 'prepared', 'applying')
        with self.journal.locked() as s:
            self.assertEqual(uj.recovery(s.read()), 'apply-uncertain')

    def test_prepare_requires_allowlisted_changed_snapshots(self):
        cases = [('gnome-animations', False, None), ('gnome-animations', 1, None),
                 ('gnome-animations', True, False), ('gnome-animations', True, 1),
                 ('power-performance', 'performance', None), ('power-performance', 'balanced', False),
                 ('power-performance', 'invalid', None), ('arbitrary', True, None)]
        with self.journal.locked() as s:
            for args in cases:
                with self.subTest(args=args), self.assertRaises(uj.CorruptJournal):
                    s.prepare(*args)
            self.assertIsNone(s.read())

    def test_bad_json_is_never_overwritten(self):
        for raw in [b'{}', b'not json', b'\xff', b'{"version":1,"version":1}',
                    b'{"version":NaN}', b'[' * 2000 + b']' * 2000, b' ' * (uj.MAX_BYTES + 1)]:
            with self.subTest(raw=raw[:40]):
                self.write_raw(raw)
                with self.journal.locked() as s:
                    with self.assertRaises(uj.CorruptJournal):
                        s.read()
                    with self.assertRaises(uj.CorruptJournal):
                        s.prepare('gnome-animations', True)
                self.assertEqual((self.path / 'undo.json').read_bytes(), raw)

    def test_strict_schema_values_and_extra_fields(self):
        r = self.seed()
        bad = [dict(r, version=True), dict(r, version=2), dict(r, extra='x'),
               dict(r, transaction='a' * 31), dict(r, transaction='A' * 32),
               dict(r, state='applied'), dict(r, previous=1), dict(r, user_value=False),
               dict(r, setting='other')]
        for record in bad:
            with self.subTest(record=record):
                self.write_raw(json.dumps(record).encode())
                with self.journal.locked() as s:
                    with self.assertRaises(uj.CorruptJournal):
                        s.read()

    def test_directory_symlink_each_component_and_ambiguous_paths(self):
        link = Path(self.tmp.name) / 'link'
        link.symlink_to(self.path, target_is_directory=True)
        for path in [link, link / 'child', str(self.path) + '/../journal', str(self.path) + '/.', 'relative', '/']:
            with self.subTest(path=path), self.assertRaises((OSError, uj.UnsafePath)):
                with uj.Journal(path).locked():
                    pass
        self.assertEqual(list(self.path.iterdir()), [])

    def test_existing_private_directory_required(self):
        os.chmod(self.path, 0o755)
        with self.assertRaises(uj.UnsafePath):
            with self.journal.locked():
                pass
        os.chmod(self.path, 0o700)
        missing = self.path / 'missing'
        with self.assertRaises(OSError):
            with uj.Journal(missing).locked():
                pass
        self.assertFalse(missing.exists())

    def test_symlink_lock_and_data_fail_closed(self):
        victim = Path(self.tmp.name) / 'victim'
        victim.write_text('untouched')
        lock = self.path / 'undo.lock'
        lock.symlink_to(victim)
        with self.assertRaises(OSError):
            with self.journal.locked():
                pass
        lock.unlink()
        data = self.path / 'undo.json'
        data.symlink_to(victim)
        with self.journal.locked() as s:
            with self.assertRaises(OSError):
                s.read()
            with self.assertRaises(OSError):
                s.prepare('gnome-animations', True)
        self.assertEqual(victim.read_text(), 'untouched')
        self.assertTrue(data.is_symlink())

    def test_symlink_final_destination_before_replace_fails_closed(self):
        r = self.seed()
        victim = Path(self.tmp.name) / 'victim'
        victim.write_text('untouched')
        with self.journal.locked() as s:
            data = self.path / 'undo.json'
            data.unlink()
            data.symlink_to(victim)
            with self.assertRaises(OSError):
                s.advance(r['transaction'], 'prepared', 'applying')
        self.assertEqual(victim.read_text(), 'untouched')

    def test_hardlink_and_insecure_file_modes_rejected(self):
        self.seed()
        data = self.path / 'undo.json'
        other = Path(self.tmp.name) / 'hardlink'
        os.link(data, other)
        with self.journal.locked() as s:
            with self.assertRaises(uj.UnsafePath):
                s.read()
        other.unlink()
        data.chmod(0o644)
        with self.journal.locked() as s:
            with self.assertRaises(uj.UnsafePath):
                s.read()

    def test_lock_hardlink_and_insecure_mode_rejected(self):
        with self.journal.locked():
            pass
        lock = self.path / 'undo.lock'
        other = Path(self.tmp.name) / 'lock-hardlink'
        os.link(lock, other)
        with self.assertRaises(uj.UnsafePath):
            with self.journal.locked():
                pass
        other.unlink()
        lock.chmod(0o644)
        with self.assertRaises(uj.UnsafePath):
            with self.journal.locked():
                pass

    def test_directory_mode_changed_during_session_is_rejected(self):
        with self.journal.locked() as s:
            self.path.chmod(0o755)
            with self.assertRaises(uj.UnsafePath):
                s.prepare('gnome-animations', True)
            self.path.chmod(0o700)
        self.assertFalse((self.path / 'undo.json').exists())

    def test_unsupported_platform_fails_closed(self):
        with patch.object(uj.sys, 'platform', 'other'):
            with self.assertRaises(uj.UnsafePath):
                with self.journal.locked():
                    pass
        self.assertEqual(list(self.path.iterdir()), [])

    def test_lock_replaced_while_held_fails_closed(self):
        with self.journal.locked() as s:
            (self.path / 'undo.lock').unlink()
            (self.path / 'undo.lock').write_bytes(b'')
            os.chmod(self.path / 'undo.lock', 0o600)
            with self.assertRaises(uj.UnsafePath):
                s.prepare('gnome-animations', True)
        self.assertFalse((self.path / 'undo.json').exists())

    def test_fifo_data_and_lock_rejected_without_blocking(self):
        fifo = self.path / 'undo.lock'
        os.mkfifo(fifo, 0o600)
        with self.assertRaises(uj.UnsafePath):
            with self.journal.locked():
                pass
        fifo.unlink()
        os.mkfifo(self.path / 'undo.json', 0o600)
        with self.journal.locked() as s:
            with self.assertRaises(uj.UnsafePath):
                s.read()

    def test_file_fsync_failure_keeps_prior_state(self):
        r = self.seed()
        with self.journal.locked() as s:
            with patch('avelin.undo_journal.os.fsync', side_effect=OSError('disk error')):
                with self.assertRaises(OSError):
                    s.advance(r['transaction'], 'prepared', 'applying')
            self.assertEqual(s.read(), r)
        self.assertEqual(sorted(p.name for p in self.path.iterdir()), ['undo.json', 'undo.lock'])

    def test_replace_error_is_uncertain_and_session_poisoned(self):
        r = self.seed()
        with self.journal.locked() as s:
            with patch('avelin.undo_journal.os.replace', side_effect=OSError('rename failure')):
                with self.assertRaises(uj.DurabilityUncertain):
                    s.advance(r['transaction'], 'prepared', 'applying')
            with self.assertRaises(uj.DurabilityUncertain):
                s.read()
        with self.journal.locked() as s:
            self.assertEqual(s.read(), r)

    def test_directory_fsync_failure_is_uncertain_even_if_visible(self):
        r = self.seed()
        real_fsync = os.fsync
        def fail_directory(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError('directory sync failed')
            return real_fsync(fd)
        with self.journal.locked() as s:
            with patch('avelin.undo_journal.os.fsync', side_effect=fail_directory):
                with self.assertRaises(uj.DurabilityUncertain):
                    s.advance(r['transaction'], 'prepared', 'applying')
            with self.assertRaises(uj.DurabilityUncertain):
                s.advance(r['transaction'], 'applying', 'verified')
        with self.journal.locked() as s:
            self.assertEqual(uj.recovery(s.read()), 'apply-uncertain')

    def test_short_writes_are_retried_and_zero_write_fails(self):
        real_write = os.write
        def short(fd, data):
            return real_write(fd, data[:3])
        with self.journal.locked() as s:
            with patch('avelin.undo_journal.os.write', side_effect=short):
                r = s.prepare('gnome-animations', True)
            with patch('avelin.undo_journal.os.write', return_value=0):
                with self.assertRaises(OSError):
                    s.advance(r['transaction'], 'prepared', 'applying')
            self.assertEqual(s.read(), r)

    def test_discard_fsync_failure_reports_uncertainty(self):
        r = self.seed()
        with self.journal.locked() as s:
            with patch('avelin.undo_journal.os.fsync', side_effect=OSError('sync failure')):
                with self.assertRaises(uj.DurabilityUncertain):
                    s.discard(r['transaction'])
            with self.assertRaises(uj.DurabilityUncertain):
                s.read()
        with self.journal.locked() as s:
            self.assertIsNone(s.read())


if __name__ == '__main__':
    unittest.main()
