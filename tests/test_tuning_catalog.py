import dataclasses
import socket
import subprocess
import unittest
from unittest.mock import patch

from avelin import tuning_catalog


class TuningCatalogTests(unittest.TestCase):
    def test_entries_are_unique_immutable_and_sourced(self):
        entries = tuning_catalog.catalog()
        self.assertIsInstance(entries, tuple)
        self.assertEqual({entry.id for entry in entries},
                         {'gnome-animations', 'compressed-swap', 'power-profiles'})
        self.assertEqual(len({entry.id for entry in entries}), len(entries))
        for entry in entries:
            with self.subTest(entry=entry.id):
                for field in ('title', 'scope', 'prerequisites', 'reversibility',
                              'risks', 'avelin_status'):
                    self.assertTrue(getattr(entry, field).strip())
                self.assertTrue(entry.source_urls)
                self.assertTrue(all(url.startswith('https://') for url in entry.source_urls))
                self.assertIn('not assessed', entry.prerequisites.lower())
                with self.assertRaises(dataclasses.FrozenInstanceError):
                    entry.title = 'changed'

    def test_read_is_static_and_does_not_access_host(self):
        with patch('builtins.open', side_effect=AssertionError('filesystem')), \
             patch('os.open', side_effect=AssertionError('filesystem')), \
             patch('os.stat', side_effect=AssertionError('filesystem')), \
             patch('os.listdir', side_effect=AssertionError('filesystem')), \
             patch('os.scandir', side_effect=AssertionError('filesystem')), \
             patch('os.getenv', side_effect=AssertionError('environment')), \
             patch.object(subprocess, 'run', side_effect=AssertionError('command')), \
             patch.object(subprocess, 'Popen', side_effect=AssertionError('process')), \
             patch.object(socket, 'socket', side_effect=AssertionError('network')):
            self.assertEqual(len(tuning_catalog.catalog()), 3)

    def test_power_hold_and_zram_recovery_are_not_claimed_reversible(self):
        entries = {entry.id: entry for entry in tuning_catalog.catalog()}
        self.assertIn('cannot recreate', entries['power-profiles'].reversibility)
        self.assertIn('cannot eliminate the race', entries['power-profiles'].reversibility)
        self.assertIn('does not recreate', entries['compressed-swap'].reversibility)
        self.assertIn('Do not change', entries['power-profiles'].avelin_status)


if __name__ == '__main__':
    unittest.main()
