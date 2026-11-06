"""Offline tests for the advisory checker's documented numeric-tag policy."""
import json
import unittest
from unittest.mock import MagicMock, patch

from avelin import updates


def release(tag, *, prerelease=False, draft=False):
    return {'tag_name': tag, 'prerelease': prerelease, 'draft': draft}


class ReleaseVersionEdges(unittest.TestCase):
    def check_releases(self, entries, installed='1.2.3'):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(entries).encode()
        with patch.object(updates, '__version__', installed), \
             patch.object(updates.urllib.request, 'urlopen', return_value=response):
            return updates.check_latest()

    def test_stable_wins_same_numeric_version_in_either_order(self):
        stable, preview = release('1.3.0'), release('v1.3.0', prerelease=True)
        for entries in ([stable, preview], [preview, stable]):
            with self.subTest(entries=entries):
                self.assertEqual(self.check_releases(entries),
                                 ('new', 'Version 1.3.0 is available.'))

    def test_newer_numeric_prerelease_beats_older_stable_and_is_labeled(self):
        entries = [release('v1.3.0'), release('v1.4.0', prerelease=True)]
        self.assertEqual(self.check_releases(entries),
                         ('new', 'Version v1.4.0 (a prerelease) is available.'))

    def test_equal_stable_or_prerelease_is_not_reported_new(self):
        for tag in ('v1.2.3', '1.2.3'):
            for preview in (False, True):
                with self.subTest(tag=tag, prerelease=preview):
                    self.assertEqual(self.check_releases([release(tag, prerelease=preview)]),
                                     ('current', 'No newer numbered release was found.'))

    def test_higher_draft_and_suffix_tags_do_not_override_stable(self):
        entries = [release('v1.3.0'), release('v90.0.0', draft=True),
                   release('v99.0.0-rc1', prerelease=True)]
        self.assertEqual(self.check_releases(entries),
                         ('new', 'Version v1.3.0 is available.'))

    def test_components_are_compared_numerically(self):
        entries = [release('v1.9.99'), release('v1.10.0')]
        self.assertEqual(self.check_releases(entries),
                         ('new', 'Version v1.10.0 is available.'))

    def test_unsupported_tags_alone_are_not_numbered_releases(self):
        for tag in ('v01.2.3', 'v1.02.3', 'v1.2.03', 'v1.2.3+build',
                    'v1.2.3-rc1', 'V1.2.3', 'v1.2', '١.2.3', ''):
            with self.subTest(tag=tag):
                self.assertEqual(self.check_releases([release(tag)]),
                                 ('none', 'No numbered releases were found.'))

    def test_whitespace_is_stripped_for_supported_tags(self):
        self.assertEqual(self.check_releases([release('  v1.3.0  ')]),
                         ('new', 'Version v1.3.0 is available.'))

    def test_malformed_metadata_makes_equal_result_inconclusive(self):
        entries = [release('v1.2.3'), {'tag_name': 'v1.4.0', 'draft': False}]
        self.assertEqual(self.check_releases(entries),
                         ('unknown', 'The release list may be incomplete; check the releases page.'))

    def test_unsupported_installed_suffix_does_not_contact_network(self):
        with patch.object(updates, '__version__', '1.2.3-rc1'), \
             patch.object(updates.urllib.request, 'urlopen') as open_url:
            self.assertEqual(updates.check_latest()[0], 'unknown')
            open_url.assert_not_called()


if __name__ == '__main__':
    unittest.main()
