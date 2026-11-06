"""Offline redirect boundary tests; no actual requests are permitted."""
import io
import json
import socket
import unittest
import urllib.request
import urllib.response
from email.message import Message
from unittest.mock import patch

from avelin import updates


class FakeServer(urllib.request.BaseHandler):
    handler_order = 100

    def __init__(self, location, loop=False):
        self.location = location
        self.loop = loop
        self.seen = []

    def https_open(self, request):
        self.seen.append(request.full_url)
        headers = Message()
        if len(self.seen) == 1 or self.loop:
            headers['Location'] = self.location
            response = urllib.response.addinfourl(io.BytesIO(b''), headers, request.full_url, 302)
            response.msg = 'Found'
        else:
            body = json.dumps([{'tag_name': 'v0.2.0', 'draft': False, 'prerelease': False}]).encode()
            response = urllib.response.addinfourl(io.BytesIO(body), headers, request.full_url, 200)
            response.msg = 'OK'
        return response

    def http_open(self, request):
        raise AssertionError('insecure destination was contacted')


class RedirectTests(unittest.TestCase):
    def check(self, location, *, loop=False):
        fake = FakeServer(location, loop=loop)
        # A real opener is used, but the high-priority fake is the only transport.
        real_builder = urllib.request.build_opener
        opener = real_builder(updates._ApiRedirectHandler(), fake)
        with patch.object(updates, '__version__', '0.1.0'), \
             patch('socket.socket.connect', side_effect=AssertionError('network blocked')), \
             patch('socket.create_connection', side_effect=AssertionError('network blocked')), \
             patch.object(updates.urllib.request, 'build_opener', return_value=opener):
            result = updates.check_latest()
        return result, fake.seen

    def test_same_host_https_and_relative_redirect_allowed(self):
        for url in ('https://api.github.com/repos/new/releases', '/repos/new/releases',
                    'https://api.github.com:443/repos/new/releases'):
            with self.subTest(url=url):
                result, seen = self.check(url)
                self.assertEqual(result, ('new', 'Version v0.2.0 is available.'))
                self.assertEqual(len(seen), 2)

    def test_downgrade_cross_host_credentials_and_port_rejected(self):
        urls = ('http://api.github.com/repos/new/releases',
                'https://untrusted.invalid/releases',
                'https://api.github.com.untrusted.invalid/releases',
                'https://api.github.com@untrusted.invalid/releases',
                'https://user@api.github.com/releases',
                'https://api.github.com:444/releases')
        for url in urls:
            with self.subTest(url=url):
                result, seen = self.check(url)
                self.assertEqual(result, ('error', 'Could not check for updates.'))
                self.assertEqual(seen, [updates.API_URL])

    def test_malformed_location_is_an_error(self):
        for url in ('https://[broken', 'https://api.github.com:bad/releases'):
            with self.subTest(url=url):
                result, seen = self.check(url)
                self.assertEqual(result[0], 'error')
                self.assertEqual(seen, [updates.API_URL])

    def test_redirect_loop_is_an_error(self):
        result, seen = self.check('https://api.github.com/loop', loop=True)
        self.assertEqual(result[0], 'error')
        self.assertLessEqual(len(seen), 11)


if __name__ == '__main__':
    unittest.main()
