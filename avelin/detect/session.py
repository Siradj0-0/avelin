"""Untrusted environment hints, not authorization to write settings.

Desktop tokens: https://specifications.freedesktop.org/desktop-entry-spec/latest/
Session hints: https://www.freedesktop.org/software/systemd/man/latest/pam_systemd.html
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class SessionHints:
    current_desktops: tuple[str, ...]
    session_desktop: str | None
    session_type: str | None


def detect_session(env: Mapping[str, str] | None = None) -> SessionHints:
    """Return separate raw desktop observations and a recognized session type.

    Unknown, absent, and unspecified session types are represented as None.
    Conflicting observations remain separate; they are not used for writes.
    """
    if env is None:
        env = os.environ
    desktop_raw = env.get('XDG_CURRENT_DESKTOP', '')
    desktops = tuple(part.strip() for part in desktop_raw.split(':') if part.strip())
    session_desktop = env.get('XDG_SESSION_DESKTOP', '').strip() or None
    if session_desktop is not None and ':' in session_desktop:
        session_desktop = None
    session_type = env.get('XDG_SESSION_TYPE', '').strip().lower()
    if session_type not in {'x11', 'wayland', 'tty', 'mir', 'web'}:
        session_type = None
    return SessionHints(desktops, session_desktop, session_type)
