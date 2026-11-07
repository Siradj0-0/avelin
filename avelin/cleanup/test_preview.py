"""Hermetic tests for the preview value contract."""
from dataclasses import FrozenInstanceError
import unittest

from avelin.cleanup.preview import Preview, PreviewStatus, RiskTier


class PreviewTests(unittest.TestCase):
    def make(self, **kw):
        data = dict(category='Cache', scope='/example/cache', risk=RiskTier.MODERATE,
                    status=PreviewStatus.COMPLETE, allocated_bytes=128, warnings=())
        data.update(kw)
        return Preview(**data)

    def test_complete_zero_is_observed_not_unknown(self):
        result = self.make(allocated_bytes=0)
        self.assertEqual(result.allocated_bytes, 0)
        self.assertIsNone(result.reclaimable_bytes)

    def test_partial_subtotal_and_unknown_are_distinct(self):
        for n in (0, 128, None):
            with self.subTest(n=n):
                result = self.make(status=PreviewStatus.PARTIAL, allocated_bytes=n,
                                   warnings=('Incomplete scan',))
                self.assertEqual(result.allocated_bytes, n)
                self.assertIsNone(result.reclaimable_bytes)

    def test_unavailable_has_no_size(self):
        p = self.make(status=PreviewStatus.UNAVAILABLE, allocated_bytes=None)
        self.assertIsNone(p.allocated_bytes)
        for n in (0, 1):
            with self.subTest(n=n), self.assertRaises(ValueError):
                self.make(status=PreviewStatus.UNAVAILABLE, allocated_bytes=n)

    def test_complete_needs_observed_size(self):
        with self.assertRaises(ValueError):
            self.make(allocated_bytes=None)

    def test_invalid_sizes(self):
        for n in (-1, True, False, 1.5, '5'):
            with self.subTest(n=n), self.assertRaises(ValueError):
                self.make(allocated_bytes=n)

    def test_nonempty_description_and_strict_enums(self):
        for patch in ({'category': ''}, {'scope': ' '}, {'risk': 'low'},
                      {'status': 'complete'}, {'scope': None}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.make(**patch)

    def test_warning_structure_is_immutable(self):
        for warnings in (['mutable'], ('',), (2,), None):
            with self.subTest(warnings=warnings), self.assertRaises(ValueError):
                self.make(warnings=warnings)
        result = self.make(warnings=('Review before cleaning',))
        with self.assertRaises(FrozenInstanceError):
            result.scope = '/elsewhere'


if __name__ == '__main__':
    unittest.main()
