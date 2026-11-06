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
    try:
        subprocess.run(['gio', 'trash', '--empty'], check=True, timeout=180, capture_output=True, text=True)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            'Emptying trash timed out. Some files may already have been permanently deleted; '
            'check the trash before taking further action.'
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            'gio reported an error while emptying trash. Some files may already have been '
            'permanently deleted; check the trash before taking further action.'
        ) from exc

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
    available, current = power_profiles()
    if profile not in available:
        raise RuntimeError('Power profile is unavailable')
    if profile == current:
        # Do not write even the same value: no manual change is needed.
        return
    # A separate ActiveProfileHolds check cannot rule out a hold acquired
    # before a subsequent set, and switching back cannot restore another
    # application's hold. Until that risk is addressed, do not issue a set.
    raise RuntimeError(
        'Changing power profiles is temporarily disabled: switching can cancel '
        "another application's profile hold, which switching back cannot restore."
    )
