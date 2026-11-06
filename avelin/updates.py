"""Release discovery only: never download or execute release artifacts."""
import http.client
import json
import re
import urllib.error
import urllib.request
from . import __version__

RELEASES_URL = 'https://github.com/Siradj0-0/avelin/releases'
API_URL = 'https://api.github.com/repos/Siradj0-0/avelin/releases?per_page=30'
MAX_RELEASES = 30
MAX_RESPONSE_BYTES = 1_000_000
TIMEOUT_SECONDS = 8
MAX_VERSION_LENGTH = 64


def version(value: str) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if len(value) > MAX_VERSION_LENGTH:
        return None
    match = re.fullmatch(r'v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value)
    return tuple(map(int, match.groups())) if match else None


def check_latest() -> tuple[str, str]:
    current = version(__version__)
    if current is None:
        return 'unknown', 'This build has an unsupported version format.'
    request = urllib.request.Request(API_URL, headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'Avelin/' + __version__,
        'X-GitHub-Api-Version': '2022-11-28',
    })
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            return 'error', 'The release list was too large to read.'
        objects = json.loads(payload)
        if not isinstance(objects, list) or len(objects) > MAX_RELEASES:
            return 'error', 'Could not read the release list.'
        candidates = []
        incomplete = len(objects) == MAX_RELEASES
        for obj in objects:
            if not isinstance(obj, dict) or not isinstance(obj.get('draft'), bool):
                incomplete = True
                continue
            if obj['draft']:
                continue
            if not isinstance(obj.get('prerelease'), bool) or not isinstance(obj.get('tag_name'), str):
                incomplete = True
                continue
            parsed = version(obj['tag_name'])
            if parsed is not None:
                candidates.append((parsed, obj['tag_name'].strip(), obj['prerelease']))
        if candidates:
            latest, tag, prerelease = max(candidates, key=lambda item: (item[0], not item[2], item[1]))
            if latest > current:
                suffix = ' (a prerelease)' if prerelease else ''
                return 'new', f'Version {tag}{suffix} is available.'
        if incomplete:
            return 'unknown', 'The release list may be incomplete; check the releases page.'
        if not candidates:
            return 'none', 'No numbered releases were found.'
        return 'current', 'No newer numbered release was found.'
    except urllib.error.HTTPError as exc:
        if exc.code == 429 or (exc.code == 403 and exc.headers and
                               (exc.headers.get('X-RateLimit-Remaining') == '0' or
                                exc.headers.get('Retry-After') is not None)):
            return 'error', 'GitHub rate limit reached; try again later.'
        return 'error', 'Could not check for updates.'
    except (OSError, ValueError, TypeError, RecursionError, http.client.HTTPException):
        return 'error', 'Could not check for updates.'
