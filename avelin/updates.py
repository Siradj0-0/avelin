"""Release discovery only: never download or execute release artifacts."""
import json
import re
import urllib.error
import urllib.request
from . import __version__

RELEASES_URL = 'https://github.com/Siradj0-0/avelin/releases'
API_URL = 'https://api.github.com/repos/Siradj0-0/avelin/releases?per_page=30'


def version(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r'v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value.strip())
    return tuple(map(int, match.groups())) if match else None


def check_latest() -> tuple[str, str]:
    request = urllib.request.Request(API_URL, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Avelin/' + __version__})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = response.read(1_000_001)
        if len(payload) > 1_000_000:
            return 'error', 'The release list was too large to read.'
        objects = json.loads(payload)
        if not isinstance(objects, list):
            return 'error', 'Could not read the release list.'
        candidates = []
        for obj in objects:
            if not isinstance(obj, dict) or obj.get('draft') is not False or not isinstance(obj.get('tag_name'), str):
                continue
            parsed = version(obj['tag_name'])
            if parsed is not None:
                candidates.append((parsed, obj['tag_name']))
        if not candidates:
            return 'none', 'No numbered releases were found.'
        current = version(__version__)
        if current is None:
            return 'unknown', 'This build has an unsupported version format.'
        latest, tag = max(candidates)
        if latest > current:
            return 'new', f'Version {tag} is available.'
        return 'current', 'No newer numbered release was found.'
    except (OSError, ValueError, TypeError):
        return 'error', 'Could not check for updates.'
