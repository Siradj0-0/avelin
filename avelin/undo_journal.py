"""Standalone, fail-closed undo journal prototype; never touches settings.

The caller supplies an existing private directory and holds a session across
journal transitions and any future external operation. See docs/undo-journal.md.
"""
from contextlib import contextmanager
import fcntl
import json
import os
import re
import secrets
import stat
import sys

MAX_BYTES = 4096
_DATA = 'undo.json'
_LOCK = 'undo.lock'
_FIELDS = frozenset(('version', 'transaction', 'setting', 'previous', 'user_value', 'state'))
_STATES = ('prepared', 'applying', 'verified', 'restoring', 'restored')
_NEXT = {'prepared': 'applying', 'applying': 'verified',
         'verified': 'restoring', 'restoring': 'restored'}
_ID = re.compile(r'[0-9a-f]{32}\Z')


class JournalError(RuntimeError):
    pass


class UnsafePath(JournalError):
    pass


class CorruptJournal(JournalError):
    pass


class Conflict(JournalError):
    pass


class Busy(JournalError):
    pass


class DurabilityUncertain(JournalError):
    """A directory mutation may have happened but was not durably confirmed."""


def _check_record(record):
    if type(record) is not dict or set(record) != _FIELDS:
        raise CorruptJournal('Invalid record fields')
    if type(record['version']) is not int or record['version'] != 1:
        raise CorruptJournal('Unsupported version')
    tx = record['transaction']
    if type(tx) is not str or not _ID.fullmatch(tx):
        raise CorruptJournal('Invalid transaction')
    state = record['state']
    if type(state) is not str or state not in _STATES:
        raise CorruptJournal('Invalid state')
    setting, previous, user = record['setting'], record['previous'], record['user_value']
    # Only changed snapshots are journaled. The fixed targets are false and
    # performance respectively; arbitrary settings/values are never accepted.
    if setting == 'gnome-animations' and type(setting) is str:
        if previous is not True or (user is not None and user is not True):
            raise CorruptJournal('Invalid animation snapshot')
    elif setting == 'power-performance' and type(setting) is str:
        if type(previous) is not str or previous not in ('balanced', 'power-saver') or user is not None:
            raise CorruptJournal('Invalid power snapshot')
    else:
        raise CorruptJournal('Setting not allowlisted')
    return record


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CorruptJournal('Duplicate JSON field')
        result[key] = value
    return result


def _reject_constant(value):
    raise CorruptJournal('Nonstandard JSON value')


def _decode(raw):
    if len(raw) > MAX_BYTES:
        raise CorruptJournal('Journal exceeds size limit')
    try:
        parsed = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_pairs,
                            parse_constant=_reject_constant)
        return _check_record(parsed)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise CorruptJournal('Invalid JSON journal') from exc


def _private_regular(fd):
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
        raise UnsafePath('File must be a private, singly linked regular file owned by this user')
    return info


def _same_entry(directory, name, info):
    try:
        entry = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError as exc:
        raise UnsafePath('Journal entry disappeared') from exc
    if not stat.S_ISREG(entry.st_mode) or (entry.st_dev, entry.st_ino) != (info.st_dev, info.st_ino):
        raise UnsafePath('Journal entry was replaced')


def _open_dir(path):
    if sys.platform != 'linux' or not all(hasattr(os, x) for x in ('O_DIRECTORY', 'O_NOFOLLOW', 'O_CLOEXEC', 'O_NONBLOCK')):
        raise UnsafePath('Required Linux file protections unavailable')
    path = os.fspath(path)
    if type(path) is not str or not path.startswith('/'):
        raise UnsafePath('An absolute directory path is required')
    parts = path.split('/')[1:]
    if not parts or any(part in ('', '.', '..') for part in parts):
        raise UnsafePath('Ambiguous directory path')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open('/', flags)
    try:
        for part in parts:
            new = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = new
        info = os.fstat(fd)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise UnsafePath('Directory must be owned by this user and mode 0700')
        return fd
    except BaseException:
        os.close(fd)
        raise


def _open_lock(directory):
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    created = False
    try:
        fd = os.open(_LOCK, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory)
        created = True
    except FileExistsError:
        fd = os.open(_LOCK, flags, dir_fd=directory)
    try:
        if created:
            os.fchmod(fd, 0o600)
        info = _private_regular(fd)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Busy('Journal is in use') from exc
        _same_entry(directory, _LOCK, info)
        return fd
    except BaseException:
        os.close(fd)
        raise


class Journal:
    """No directory creation, environment lookup, settings reads or writes."""
    def __init__(self, directory):
        self._directory = directory

    @contextmanager
    def locked(self):
        """Hold the exclusive lock across a complete future external operation."""
        directory = _open_dir(self._directory)
        lock = None
        session = None
        try:
            lock = _open_lock(directory)
            session = _Session(directory, lock)
            yield session
        finally:
            if session is not None:
                session._closed = True
            if lock is not None:
                os.close(lock)
            os.close(directory)


class _Session:
    def __init__(self, directory, lock):
        self._directory, self._lock, self._closed = directory, lock, False
        self._uncertain = False

    def _check(self):
        if self._closed:
            raise JournalError('Session is closed')
        if self._uncertain:
            raise DurabilityUncertain('Close and reopen the session to inspect the journal')
        info = os.fstat(self._directory)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise UnsafePath('Journal directory is no longer private')
        _same_entry(self._directory, _LOCK, _private_regular(self._lock))

    def read(self):
        """Return the validated record, or None if no journal exists."""
        self._check()
        try:
            fd = os.open(_DATA, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=self._directory)
        except FileNotFoundError:
            return None
        try:
            info = _private_regular(fd)
            _same_entry(self._directory, _DATA, info)
            if info.st_size > MAX_BYTES:
                raise CorruptJournal('Journal exceeds size limit')
            chunks, remaining = [], MAX_BYTES + 1
            while remaining:
                chunk = os.read(fd, remaining)
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            return _decode(b''.join(chunks))
        finally:
            os.close(fd)

    def prepare(self, setting, previous, user_value=None):
        """Persist a new changed snapshot before a future external operation."""
        self._check()
        if self.read() is not None:
            raise Conflict('An unresolved transaction already exists')
        record = {'version': 1, 'transaction': secrets.token_hex(16), 'setting': setting,
                  'previous': previous, 'user_value': user_value, 'state': 'prepared'}
        _check_record(record)
        self._persist(record)
        return record.copy()

    def advance(self, transaction, expected, next_state):
        """Persist exactly one valid transition under the held lock."""
        self._check()
        if type(transaction) is not str or not _ID.fullmatch(transaction):
            raise Conflict('Invalid transaction')
        if type(expected) is not str or type(next_state) is not str or _NEXT.get(expected) != next_state:
            raise Conflict('Invalid transition')
        record = self.read()
        if record is None or record['transaction'] != transaction or record['state'] != expected:
            raise Conflict('Transaction or state changed')
        record['state'] = next_state
        self._persist(record)
        return record.copy()

    def resolve_uncertain(self, transaction, expected, outcome):
        """Record an explicit operator-reviewed outcome; never inspect settings.

        Only call after independently verifying the outcome. An external change
        can race that verification; this method cannot prove it was correct.
        """
        self._check()
        choices = {('applying', 'not-applied'): 'prepared',
                   ('applying', 'applied'): 'verified',
                   ('restoring', 'not-restored'): 'verified',
                   ('restoring', 'restored'): 'restored'}
        if (type(transaction) is not str or not _ID.fullmatch(transaction)
                or type(expected) is not str or type(outcome) is not str
                or (expected, outcome) not in choices):
            raise Conflict('Invalid recovery outcome')
        record = self.read()
        if record is None or record['transaction'] != transaction or record['state'] != expected:
            raise Conflict('Transaction or state changed')
        record['state'] = choices[(expected, outcome)]
        self._persist(record)
        return record.copy()

    def discard(self, transaction):
        """Remove only a never-applied or confirmed-restored transaction."""
        self._check()
        record = self.read()
        if (record is None or type(transaction) is not str or transaction != record['transaction']
                or record['state'] not in ('prepared', 'restored')):
            raise Conflict('Only prepared or restored transactions can be discarded')
        self._check()
        try:
            os.unlink(_DATA, dir_fd=self._directory)
            os.fsync(self._directory)
        except OSError as exc:
            self._uncertain = True
            raise DurabilityUncertain('Discard may have occurred; reopen and inspect') from exc

    def _persist(self, record):
        self._check()
        _check_record(record)
        data = json.dumps(record, ensure_ascii=True, separators=(',', ':'), sort_keys=True).encode('ascii')
        if len(data) > MAX_BYTES:
            raise CorruptJournal('Journal exceeds size limit')
        name = '.undo-' + secrets.token_hex(16) + '.tmp'
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        fd = os.open(name, flags, 0o600, dir_fd=self._directory)
        renamed = False
        try:
            os.fchmod(fd, 0o600)
            info = _private_regular(fd)
            offset = 0
            while offset < len(data):
                written = os.write(fd, data[offset:])
                if written <= 0:
                    raise OSError('Short journal write')
                offset += written
            os.fsync(fd)
            self._check()
            _same_entry(self._directory, name, info)
            # Validate any existing destination immediately before replace.
            self.read()
            try:
                os.replace(name, _DATA, src_dir_fd=self._directory, dst_dir_fd=self._directory)
                renamed = True
                os.fsync(self._directory)
            except OSError as exc:
                self._uncertain = True
                raise DurabilityUncertain('Journal commit may have occurred; reopen and inspect') from exc
        finally:
            os.close(fd)
            if not renamed:
                try:
                    _same_entry(self._directory, name, info)
                    os.unlink(name, dir_fd=self._directory)
                except (FileNotFoundError, UnsafePath, UnboundLocalError):
                    pass


def recovery(record):
    """Classify only; does not read a system setting or change the journal."""
    if record is None:
        return 'empty'
    _check_record(record)
    return {'prepared': 'not-started', 'applying': 'apply-uncertain',
            'verified': 'undo-needs-current-state-check', 'restoring': 'restore-uncertain',
            'restored': 'complete'}[record['state']]
