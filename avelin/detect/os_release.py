"""Read the current process's os-release view without executing shell code.

Format and fallback: https://www.freedesktop.org/software/systemd/man/latest/os-release.html
This describes the visible environment, not necessarily the host OS.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

_KEY = re.compile(r"[A-Z][A-Z_0-9]*\Z")
_UNQUOTED = re.compile(r"[A-Za-z0-9._-]*\Z")


def _value(raw: str) -> str | None:
    if not raw:
        return ""
    if raw[0] == "'":
        if len(raw) < 2 or raw[-1] != "'" or "'" in raw[1:-1]:
            return None
        return raw[1:-1]
    if raw[0] != '"':
        return raw if _UNQUOTED.fullmatch(raw) else None
    if len(raw) < 2 or raw[-1] != '"':
        return None
    body = raw[1:-1]
    chars = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == '"' or ch in '$`':
            return None
        if ch == '\\':
            i += 1
            if i >= len(body):
                return None
            if body[i] not in '\\"$`':
                chars.append('\\')
            ch = body[i]
        chars.append(ch)
        i += 1
    return ''.join(chars)


def parse_os_release(text: str) -> dict[str, str]:
    """Parse valid assignments; invalid later duplicates invalidate the key."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        key, sep, raw = line.partition('=')
        if not sep or not _KEY.fullmatch(key):
            continue
        value = _value(raw)
        if value is None:
            result.pop(key, None)
        else:
            result[key] = value
    return result


def read_os_release(etc: str | Path = '/etc/os-release',
                    vendor: str | Path = '/usr/lib/os-release') -> dict[str, str] | None:
    """Use vendor only if etc is absent; None means the source was unavailable."""
    try:
        try:
            text = Path(etc).read_text(encoding='utf-8')
        except FileNotFoundError:
            text = Path(vendor).read_text(encoding='utf-8')
    except (OSError, UnicodeError, ValueError):
        return None
    return parse_os_release(text)


def distribution_name(fields: Mapping[str, str] | None) -> str | None:
    """Return a nonempty display name, or None if unavailable."""
    if fields is None:
        return None
    return fields.get('PRETTY_NAME', '').strip() or None
