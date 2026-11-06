"""Offline regression tests for bounded, advisory release checking."""
import http.client
import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from avelin import updates


def release(tag, *, draft=False, prerelease=False):
    return {'tag_name': tag, 'draft': draft, 'prerelease': prerelease}


class UpdateReliabilityTests(unittest.TestCase):
    def setUp(self):
        version_patch = patch.object(updates, '__version__', '0.1.0')
        version_patch.start()
        self.addCleanup(version_patch.stop)

    def check(self, data):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = data
        with patch.object(updates.urllib.request, 'urlopen', return_value=response) as open_url:
            result = updates.check_latest()
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, updates.API_URL)
        self.assertEqual(open_url.call_args.kwargs['timeout'], updates.TIMEOUT_SECONDS)
        self.assertEqual(request.get_header('Accept'), 'application/vnd.github+json')
        self.assertEqual(request.get_header('X-github-api-version'), '2022-11-28')
        response.__enter__.return_value.read.assert_called_once_with(updates.MAX_RESPONSE_BYTES + 1)
        return result

    def test_numeric_versions_are_bounded_and_ascii(self):
        for bad in (None, '', 'v01.2.3', '1.2.3-rc1', '١.2.3', '1.' + '9' * 10000 + '.0'):
            with self.subTest(bad=str(bad)[:40]):
                self.assertIsNone(updates.version(bad))
        self.assertEqual(updates.version(' v10.2.3 '), (10, 2, 3))

    def test_greatest_numeric_version_and_draft_exclusion(self):
        data = [release('v0.2.0'), release('v0.10.0'), release('v99.0.0', draft=True),
                release('v0.11.0-rc1')]
        status, message = self.check(json.dumps(data).encode())
        self.assertEqual(status, 'new')
        self.assertIn('v0.10.0', message)
        self.assertNotIn('v99.0.0', message)

    def test_numbered_prerelease_is_identified(self):
        status, message = self.check(json.dumps([release('v0.2.0', prerelease=True)]).encode())
        self.assertEqual(status, 'new')
        self.assertIn('prerelease', message)

    def test_current_and_no_numbered_release(self):
        self.assertEqual(self.check(json.dumps([release('v0.1.0')]).encode())[0], 'current')
        self.assertEqual(self.check(json.dumps([release('v0.3.0-rc1')]).encode())[0], 'none')
        self.assertEqual(self.check(b'[]')[0], 'none')

    def test_full_page_is_not_claimed_current_or_empty(self):
        self.assertEqual(self.check(json.dumps([release('v0.1.0')] * 30).encode())[0], 'unknown')
        self.assertEqual(self.check(json.dumps([release('bad')] * 30).encode())[0], 'unknown')
        self.assertEqual(self.check(json.dumps([release('v0.2.0')] * 30).encode())[0], 'new')

    def test_malformed_entry_makes_negative_result_inconclusive(self):
        for item in (None, {}, {'draft': False, 'tag_name': 'v0.1.0'},
                     {'draft': False, 'prerelease': 'false', 'tag_name': 'v0.1.0'}):
            with self.subTest(item=item):
                self.assertEqual(self.check(json.dumps([item]).encode())[0], 'unknown')
        self.assertEqual(self.check(json.dumps([{}, release('v0.2.0')]).encode())[0], 'new')

    def test_malformed_or_large_payloads(self):
        for data in (b'{', b'\xff', b'{}', b'null', b'x' * (updates.MAX_RESPONSE_BYTES + 1),
                     json.dumps([release('v0.1.0')] * 31).encode()):
            with self.subTest(size=len(data)):
                self.assertEqual(self.check(data)[0], 'error')

    def test_deeply_nested_payload_is_inconclusive_or_an_error(self):
        self.assertIn(self.check(b'[' * 2000 + b']' * 2000)[0], ('unknown', 'error'))

    def test_same_version_prefers_stable_over_prerelease(self):
        data = [release('v0.2.0', prerelease=True), release('0.2.0')]
        status, message = self.check(json.dumps(data).encode())
        self.assertEqual(status, 'new')
        self.assertNotIn('prerelease', message)

    def test_http_and_network_failures_are_safe(self):
        errors = [
            (urllib.error.HTTPError(updates.API_URL, 429, 'limit', {}, io.BytesIO()), 'rate limit'),
            (urllib.error.HTTPError(updates.API_URL, 403, 'limit', {'X-RateLimit-Remaining': '0'}, io.BytesIO()), 'rate limit'),
            (urllib.error.HTTPError(updates.API_URL, 403, 'limit', {'Retry-After': '60'}, io.BytesIO()), 'rate limit'),
            (urllib.error.HTTPError(updates.API_URL, 403, 'forbidden', {}, io.BytesIO()), 'Could not'),
            (urllib.error.HTTPError(updates.API_URL, 500, 'server', {}, io.BytesIO()), 'Could not'),
            (urllib.error.URLError('sensitive network detail'), 'Could not'),
            (TimeoutError('sensitive detail'), 'Could not'),
            (http.client.IncompleteRead(b'{'), 'Could not'),
        ]
        for error, fragment in errors:
            with self.subTest(error=error), patch.object(updates.urllib.request, 'urlopen', side_effect=error) as open_url:
                status, message = updates.check_latest()
                self.assertEqual(status, 'error')
                self.assertIn(fragment, message)
                self.assertNotIn('sensitive', message)
                open_url.assert_called_once()

    def test_response_read_failure_closes_response(self):
        response = MagicMock()
        response.__enter__.return_value.read.side_effect = http.client.IncompleteRead(b'{')
        with patch.object(updates.urllib.request, 'urlopen', return_value=response):
            self.assertEqual(updates.check_latest()[0], 'error')
        response.__exit__.assert_called_once()

    def test_unsupported_installed_version_avoids_network(self):
        with patch.object(updates, '__version__', '0.2.0-dev'), patch.object(updates.urllib.request, 'urlopen') as open_url:
            self.assertEqual(updates.check_latest()[0], 'unknown')
            open_url.assert_not_called()


if __name__ == '__main__':
    unittest.main()
