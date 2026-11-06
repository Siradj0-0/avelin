"""Narrow, explicit actions; no shell, root escalation, or automatic cleanup."""
import os
import shutil
import subprocess

SCHEMA = 'org.gnome.desktop.interface'
KEY = 'enable-animations'


def animation_state() -> bool | None:
    if 'gnome' not in os.environ.get('XDG_CURRENT_DESKTOP', '').lower() or not shutil.which('gsettings'):
        return None
    try:
        result = subprocess.run(['gsettings', 'get', SCHEMA, KEY], capture_output=True, text=True, timeout=4, check=True).stdout.strip()
        return {'true': True, 'false': False}.get(result)
    except (OSError, subprocess.SubprocessError):
        return None


def set_animations(enabled: bool) -> None:
    if animation_state() is None:
        raise RuntimeError('GNOME animation setting is unavailable')
    subprocess.run(['gsettings', 'set', SCHEMA, KEY, 'true' if enabled else 'false'], check=True, timeout=5, capture_output=True, text=True)
    if animation_state() != enabled:
        raise RuntimeError('Could not verify the animation setting')


def empty_trash() -> None:
    if not shutil.which('gio'):
        raise RuntimeError('The gio command is not installed')
    subprocess.run(['gio', 'trash', '--empty'], check=True, timeout=180, capture_output=True, text=True)
