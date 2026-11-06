"""SQLite history tests use only temporary databases and injected failures."""
from pathlib import Path
import sqlite3
import tempfile
import unittest

from .sqlite_history import HistoryStorageError, SQLiteHistory


class SQLiteHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'history.sqlite'
        self.connection = sqlite3.connect(self.path, timeout=0)
        self.addCleanup(self.connection.close)

    def test_persists_range_order_and_zero_vs_gap(self):
        store = SQLiteHistory(self.connection, max_rows=8, per_series=4)
        for timestamp, value in [(3, None), (1, 0), (3, 2)]:
            store.append('cpu', timestamp, value)
        self.connection.close()
        self.connection = sqlite3.connect(self.path, timeout=0)
        self.addCleanup(self.connection.close)
        reopened = SQLiteHistory(self.connection, max_rows=8, per_series=4)
        self.assertEqual(reopened.range('cpu', 1, 3), ((1.0, 0.0), (3.0, None), (3.0, 2.0)))

    def test_global_and_per_series_retention_by_insertion_order(self):
        store = SQLiteHistory(self.connection, max_rows=3, per_series=2)
        store.append('cpu', 10, 1)
        store.append('cpu', 5, None)
        store.append('cpu', 7, 0)
        store.append('ram', 9, 9)
        store.append('disk', 3, 4)
        self.assertEqual(store.range('cpu', 0, 20), ((7.0, 0.0),))
        self.assertEqual(store.range('ram', 0, 20), ((9.0, 9.0),))
        self.assertEqual(store.range('disk', 0, 20), ((3.0, 4.0),))

    def test_unrelated_database_rejected_without_modification(self):
        self.connection.execute('CREATE TABLE unrelated (value TEXT)')
        self.connection.execute("INSERT INTO unrelated VALUES ('keep')")
        self.connection.commit()
        with self.assertRaises(HistoryStorageError):
            SQLiteHistory(self.connection)
        self.assertEqual(self.connection.execute('SELECT value FROM unrelated').fetchone(), ('keep',))

    def test_locked_and_read_only_writes_report_failure(self):
        store = SQLiteHistory(self.connection)
        store.append('cpu', 1, 1)
        other = sqlite3.connect(self.path, timeout=0)
        self.addCleanup(other.close)
        other.execute('BEGIN EXCLUSIVE')
        try:
            with self.assertRaises(HistoryStorageError):
                store.append('cpu', 2, 2)
        finally:
            other.rollback()
        self.assertEqual(store.range('cpu', 0, 10), ((1.0, 1.0),))
        self.connection.execute('PRAGMA query_only = ON')
        with self.assertRaises(HistoryStorageError):
            store.append('cpu', 2, 2)
        self.assertEqual(store.range('cpu', 0, 10), ((1.0, 1.0),))

    def test_external_transaction_is_not_committed_or_rolled_back(self):
        store = SQLiteHistory(self.connection)
        self.connection.execute('BEGIN')
        with self.assertRaises(HistoryStorageError):
            store.append('cpu', 1, 1)
        self.assertTrue(self.connection.in_transaction)
        self.connection.rollback()

    def test_failure_after_insert_rolls_back_retention_and_new_sample(self):
        store = SQLiteHistory(self.connection, max_rows=2, per_series=2)
        store.append('cpu', 1, 7)
        def deny_delete(action, _one, _two, _db, _trigger):
            return sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_DELETE else sqlite3.SQLITE_OK
        self.connection.set_authorizer(deny_delete)
        try:
            with self.assertRaises(HistoryStorageError):
                store.append('cpu', 2, 8)
        finally:
            self.connection.set_authorizer(None)
        self.assertEqual(store.range('cpu', 0, 10), ((1.0, 7.0),))

    def test_corrupt_database_is_reported_and_file_left_in_place(self):
        path = Path(self.temp.name) / 'corrupt.sqlite'
        data = b'not a SQLite database'
        path.write_bytes(data)
        connection = sqlite3.connect(path, timeout=0)
        self.addCleanup(connection.close)
        with self.assertRaises(HistoryStorageError):
            SQLiteHistory(connection)
        self.assertEqual(path.read_bytes(), data)

    def test_stricter_limits_reject_existing_data_without_pruning(self):
        store = SQLiteHistory(self.connection, max_rows=3, per_series=3)
        store.append('cpu', 1, 1)
        store.append('cpu', 2, 2)
        with self.assertRaises(HistoryStorageError):
            SQLiteHistory(self.connection, max_rows=1, per_series=1)
        self.assertEqual(store.range('cpu', 0, 10), ((1.0, 1.0), (2.0, 2.0)))

    def test_database_full_reports_failure_and_preserves_prior_samples(self):
        self.connection.execute('PRAGMA page_size = 512')
        store = SQLiteHistory(self.connection, max_rows=1000, per_series=1000)
        pages = self.connection.execute('PRAGMA page_count').fetchone()[0]
        self.connection.execute(f'PRAGMA max_page_count = {pages}')
        previous = ()
        for timestamp in range(1000):
            try:
                store.append('cpu', timestamp, timestamp)
            except HistoryStorageError as exc:
                self.assertIsInstance(exc.__cause__, sqlite3.Error)
                code = getattr(exc.__cause__, 'sqlite_errorcode', None)
                if code is not None:  # attribute is not available on Python 3.10
                    self.assertEqual(code, sqlite3.SQLITE_FULL)
                break
            previous = store.range('cpu', 0, 1000)
        else:
            self.fail('fixture did not reach SQLITE_FULL')
        self.assertEqual(store.range('cpu', 0, 1000), previous)

    def test_closed_connection_is_reported(self):
        store = SQLiteHistory(self.connection)
        self.connection.close()
        with self.assertRaises(HistoryStorageError):
            store.append('cpu', 1, 1)
        with self.assertRaises(HistoryStorageError):
            store.range('cpu', 0, 2)

    def test_invalid_values_limits_and_range(self):
        with self.assertRaises(ValueError):
            SQLiteHistory(self.connection, max_rows=1, per_series=2)
        store = SQLiteHistory(self.connection, max_rows=2, per_series=1)
        for timestamp, value in [(-1, 0), (float('nan'), 0), (1, float('inf')), (1, True)]:
            with self.subTest(timestamp=timestamp, value=value), self.assertRaises(ValueError):
                store.append('cpu', timestamp, value)
        with self.assertRaises(ValueError):
            store.range('cpu', 3, 2)
        self.assertEqual(store.range('cpu', 0, 10), ())


if __name__ == '__main__':
    unittest.main()
