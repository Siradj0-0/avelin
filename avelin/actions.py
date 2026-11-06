"""Narrow, allowlisted actions; no shell, root escalation, or automatic cleanup."""
from dataclasses import dataclass
import os
import shutil
import subprocess

SCHEMA = 'org.gnome.desktop.interface'


@dataclass(frozen=True)
class Setting:
    key: str
    title: str
    description: str
    group: str


SETTINGS = (
    Setting('enable-animations', 'Desktop animations', 'Turn off visual effects to reduce animation work. Effects depend on your desktop.', 'Appearance'),
    Setting('enable-hot-corners', 'Hot corner', 'Open the activities overview from the upper-left corner.', 'Interaction'),
    Setting('clock-show-seconds', 'Clock seconds', 'Show seconds in the top-bar clock.', 'Clock and status'),
    Setting('clock-show-date', 'Clock date', 'Show the date beside the time.', 'Clock and status'),
    Setting('clock-show-weekday', 'Clock weekday', 'Show the day of the week beside the time.', 'Clock and status'),
    Setting('show-battery-percentage', 'Battery percentage', 'Show battery percentage in the status menu.', 'Clock and status'),
    Setting('cursor-blink', 'Blinking cursor', 'Allow the text cursor to blink.', 'Accessibility'),
)
ALLOWED_KEYS = frozenset(item.key for item in SETTINGS)


def setting_state(key: str) -> bool | None:
    if key not in ALLOWED_KEYS:
        raise ValueError('Setting is not allowlisted')
    if 'gnome' not in os.environ.get('XDG_CURRENT_DESKTOP', '').lower() or not shutil.which('gsettings'):
        return None
    try:
        result = subprocess.run(['gsettings', 'get', SCHEMA, key], capture_output=True, text=True, timeout=4, check=True).stdout.strip()
        return {'true': True, 'false': False}.get(result)
    except (OSError, subprocess.SubprocessError):
        return None


def set_setting(key: str, enabled: bool) -> None:
    if setting_state(key) is None:
        raise RuntimeError('This GNOME setting is unavailable')
    subprocess.run(['gsettings', 'set', SCHEMA, key, 'true' if enabled else 'false'], check=True, timeout=5, capture_output=True, text=True)
    if setting_state(key) != enabled:
        raise RuntimeError('Could not verify the setting')


def empty_trash() -> None:
    if not shutil.which('gio'):
        raise RuntimeError('The gio command is not installed')
    subprocess.run(['gio', 'trash', '--empty'], check=True, timeout=180, capture_output=True, text=True)

POWER_PROFILES = frozenset(('power-saver', 'balanced', 'performance'))


def power_profiles() -> tuple[list[str], str | None]:
    """Discover daemon-advertised profiles and current profile, or report unavailable."""
    if not shutil.which('powerprofilesctl'):
        return [], None
    try:
        listing = subprocess.run(['powerprofilesctl', 'list'], capture_output=True, text=True, timeout=5, check=True).stdout
        current = subprocess.run(['powerprofilesctl', 'get'], capture_output=True, text=True, timeout=5, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return [], None
    import re
    found = []
    for line in listing.splitlines():
        match = re.fullmatch(r'\s*\*?\s*(power-saver|balanced|performance):\s*', line)
        if match and match.group(1) not in found:
            found.append(match.group(1))
    return (found, current) if current in found else ([], None)


def set_power_profile(profile: str) -> None:
    if profile not in POWER_PROFILES:
        raise ValueError('Power profile is not allowlisted')
    available, _ = power_profiles()
    if profile not in available:
        raise RuntimeError('Power profile is unavailable')
    subprocess.run(['powerprofilesctl', 'set', profile], capture_output=True, text=True, timeout=20, check=True)
    if power_profiles()[1] != profile:
        raise RuntimeError('Could not verify the power profile')
