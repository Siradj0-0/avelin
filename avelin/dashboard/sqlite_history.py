"""Experimental SQLite history; callers own the dedicated connection.

Timestamps are Unix seconds supplied by the caller. Retention is by insertion
order, not wall-clock order. No files are opened or deleted by this module.
Row limits are logical limits, not a bound on database or journal file bytes.
This prototype is synchronous and must not run on the GTK main thread.
"""
import sqlite3

from .history import History


class HistoryStorageError(Exception):
    """History is unavailable; callers must not display a fabricated value."""


_APP_ID = 0x41564C4E
_VERSION = 1
_TABLE = ('CREATE TABLE samples (id INTEGER PRIMARY KEY, series TEXT NOT NULL, '
          'timestamp REAL NOT NULL, value REAL)')
_INDEX = 'CREATE INDEX samples_series_id ON samples(series, id)'
_EXPECTED = [('index', 'samples_series_id', _INDEX), ('table', 'samples', _TABLE)]


class SQLiteHistory:
    """Bound rows in a dedicated, caller-owned SQLite connection.

    `None` denotes a gap; zero remains a value. Do not share the connection
    across threads or use it for unrelated data. Reject existing foreign or
    incompatible schemas without modifying them. If stricter limits are given
    on reopen, reject over-limit data instead of silently deleting it.
    """

    def __init__(self, connection, max_rows=5000, per_series=300):
        if (type(max_rows) is not int or not 1 <= max_rows <= 10000 or
                type(per_series) is not int or not 1 <= per_series <= max_rows):
            raise ValueError('history limits out of range')
        self.connection = connection
        self.max_rows = max_rows
        self.per_series = per_series
        self._initialize()

    def _require_idle(self):
        try:
            active = self.connection.in_transaction
        except sqlite3.Error as exc:
            raise HistoryStorageError('history connection unavailable') from exc
        if active:
            raise HistoryStorageError('connection already has an active transaction')

    def _initialize(self):
        self._require_idle()
        started = False
        try:
            self.connection.execute('BEGIN IMMEDIATE')
            started = True
            app_id = self.connection.execute('PRAGMA application_id').fetchone()[0]
            version = self.connection.execute('PRAGMA user_version').fetchone()[0]
            objects = self.connection.execute(
                "SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
            ).fetchall()
            if app_id == 0 and version == 0 and not objects:
                self.connection.execute(_TABLE)
                self.connection.execute(_INDEX)
                self.connection.execute(f'PRAGMA application_id = {_APP_ID}')
                self.connection.execute(f'PRAGMA user_version = {_VERSION}')
            elif app_id != _APP_ID or version != _VERSION or objects != _EXPECTED:
                raise HistoryStorageError('foreign or incompatible history database')
            total = self.connection.execute('SELECT COUNT(*) FROM samples').fetchone()[0]
            too_many = self.connection.execute(
                'SELECT 1 FROM samples GROUP BY series HAVING COUNT(*) > ? LIMIT 1',
                (self.per_series,)).fetchone()
            if total > self.max_rows or too_many:
                raise HistoryStorageError('existing history exceeds configured limits')
            self.connection.commit()
        except (sqlite3.Error, HistoryStorageError) as exc:
            if started and self.connection.in_transaction:
                try:
                    self.connection.rollback()
                except sqlite3.Error:
                    pass
            if isinstance(exc, HistoryStorageError):
                raise
            raise HistoryStorageError('unable to initialize history') from exc

    def append(self, name, timestamp, value):
        History._name(name)
        timestamp = History._number(timestamp, nonnegative=True)
        value = None if value is None else History._number(value)
        self._require_idle()
        started = False
        try:
            self.connection.execute('BEGIN IMMEDIATE')
            started = True
            self.connection.execute('INSERT INTO samples (series, timestamp, value) VALUES (?, ?, ?)',
                                    (name, timestamp, value))
            self.connection.execute('DELETE FROM samples WHERE series = ? AND id NOT IN '
                                    '(SELECT id FROM samples WHERE series = ? ORDER BY id DESC LIMIT ?)',
                                    (name, name, self.per_series))
            self.connection.execute('DELETE FROM samples WHERE id NOT IN '
                                    '(SELECT id FROM samples ORDER BY id DESC LIMIT ?)', (self.max_rows,))
            self.connection.commit()
        except sqlite3.Error as exc:
            if started and self.connection.in_transaction:
                try:
                    self.connection.rollback()
                except sqlite3.Error:
                    pass
            raise HistoryStorageError('unable to store history sample') from exc

    def range(self, name, start, end):
        History._name(name)
        start = History._number(start, nonnegative=True)
        end = History._number(end, nonnegative=True)
        if end < start:
            raise ValueError('range end precedes start')
        try:
            return tuple(self.connection.execute(
                'SELECT timestamp, value FROM samples WHERE series = ? AND timestamp >= ? AND timestamp <= ? '
                'ORDER BY timestamp, id LIMIT ?', (name, start, end, self.per_series)).fetchall())
        except sqlite3.Error as exc:
            raise HistoryStorageError('unable to read history') from exc
