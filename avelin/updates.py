"""Release discovery only: never download or execute release artifacts."""
import json
import re
import urllib.error
import urllib.request
from . import __version__

RELEASES_URL = 'https://github.com/Siradj0-0/avelin/releases'
API_URL = 'https://api.github.com/repos/Siradj0-0/avelin/releases/latest'


def version(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r'v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value.strip())
    return tuple(map(int, match.groups())) if match else None


def check_latest() -> tuple[str, str]:
    request = urllib.request.Request(API_URL, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Avelin/' + __version__})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            obj = json.load(response)
        latest = version(str(obj.get('tag_name', '')))
        current = version(__version__)
        if latest is None or current is None:
            return 'unknown', 'The latest release has an unsupported version format.'
        if latest > current:
            return 'new', f'Version {obj["tag_name"]} is available.'
        return 'current', 'You have the latest release.'
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return 'none', 'There are no published releases yet.'
        return 'error', 'Could not check for updates.'
    except (OSError, ValueError, TypeError):
        return 'error', 'Could not check for updates.'
