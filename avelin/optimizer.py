"""Opt-in, narrowly scoped optimizations. No mutation happens on import or probe.

Call prepare(), retain its returned snapshot, then apply(snapshot); restore(snapshot)
can be attempted even if apply raised after starting a write. See the catalog.
"""
from dataclasses import dataclass
import os
import re
import shutil
import subprocess
import sys

ANIMATIONS = 'gnome-animations'
PERFORMANCE = 'power-performance'
_IDS = frozenset((ANIMATIONS, PERFORMANCE))
_PROFILES = frozenset(('power-saver', 'balanced', 'performance'))
_SCHEMA = 'org.gnome.desktop.interface'
_KEY = 'enable-animations'


class Unavailable(RuntimeError):
    """The platform, capability, permissions, or service is unavailable."""


class Conflict(RuntimeError):
    """State changed since the snapshot; refusing to overwrite it."""


@dataclass(frozen=True)
class Snapshot:
    """Retain securely, in the same user/session, until restoration is complete."""
    setting: str
    previous: bool | str
    user_value: bool | None = None
    changed: bool = True


def _validate(snapshot):
    if not isinstance(snapshot, Snapshot) or snapshot.setting not in _IDS:
        raise ValueError('Unknown optimization snapshot')
    if type(snapshot.changed) is not bool:
        raise ValueError('Invalid snapshot')
    if snapshot.setting == ANIMATIONS:
        if type(snapshot.previous) is not bool or (snapshot.user_value is not None and type(snapshot.user_value) is not bool):
            raise ValueError('Invalid animation snapshot')
        if snapshot.changed != (snapshot.previous is not False):
            raise ValueError('Invalid animation snapshot')
    elif (snapshot.previous not in _PROFILES or snapshot.user_value is not None
          or snapshot.changed != (snapshot.previous != 'performance')):
        raise ValueError('Invalid power snapshot')


def _gnome_settings():
    if sys.platform != 'linux' or 'gnome' not in os.environ.get('XDG_CURRENT_DESKTOP', '').lower().split(':'):
        raise Unavailable('A GNOME Linux session is required')
    try:
        from gi.repository import Gio
        source = Gio.SettingsSchemaSource.get_default()
        schema = source.lookup(_SCHEMA, True) if source else None
        if not schema or not schema.has_key(_KEY) or schema.get_key(_KEY).get_value_type().dup_string() != 'b':
            raise Unavailable('GNOME animation setting is unavailable')
        settings = Gio.Settings.new_full(schema, None, None)
        if not settings.is_writable(_KEY):
            raise Unavailable('GNOME animation setting is locked')
        return settings
    except Unavailable:
        raise
    except Exception as exc:
        raise Unavailable('GSettings is unavailable') from exc


def _animation_state():
    settings = _gnome_settings()
    try:
        effective = settings.get_boolean(_KEY)
        variant = settings.get_user_value(_KEY)
        user = None if variant is None else variant.unpack()
        if type(effective) is not bool or (user is not None and type(user) is not bool):
            raise ValueError('Unexpected GSettings value')
        return settings, effective, user
    except Exception as exc:
        raise Unavailable('Cannot read GNOME animation setting') from exc


def _power_command(operation, profile=None):
    # The only executable and arguments accepted anywhere in this module.
    if operation not in ('list', 'get', 'set') or (operation == 'set' and profile not in _PROFILES) or (operation != 'set' and profile is not None):
        raise ValueError('Command not allowlisted')
    if sys.platform != 'linux':
        raise Unavailable('Linux is required')
    executable = shutil.which('powerprofilesctl')
    if not executable:
        raise Unavailable('powerprofilesctl is not installed')
    args = [executable, operation] + ([profile] if operation == 'set' else [])
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise Unavailable('Power profile command failed or timed out; a change may have occurred') from exc


def _power_state():
    listing = _power_command('list')
    found = set()
    for line in listing.splitlines():
        match = re.fullmatch(r'\s*\*?\s*(power-saver|balanced|performance):\s*', line)
        if match:
            found.add(match.group(1))
    current = _power_command('get').strip()
    if current not in found:
        raise Unavailable('Power profile service returned an unsupported state')
    return found, current


def prepare(setting):
    """Probe and capture the pre-change state. Does not change any setting."""
    if setting not in _IDS:
        raise ValueError('Unknown optimization')
    if setting == ANIMATIONS:
        _, current, user = _animation_state()
        return Snapshot(setting, current, user, current is not False)
    available, current = _power_state()
    if 'performance' not in available:
        raise Unavailable('Performance profile is not advertised')
    return Snapshot(setting, current, None, current != 'performance')


def apply(snapshot):
    """Explicitly apply a prepared setting, refusing stale state; verify result."""
    _validate(snapshot)
    if snapshot.setting == ANIMATIONS:
        settings, current, user = _animation_state()
        if (current, user) != (snapshot.previous, snapshot.user_value):
            raise Conflict('Animation state changed since preparation')
        if not snapshot.changed:
            return
        try:
            if not settings.set_boolean(_KEY, False):
                raise Unavailable('Animation write was rejected; retain snapshot')
        except Unavailable:
            raise
        except Exception as exc:
            raise Unavailable('Animation write failed; retain snapshot') from exc
        _, effective, new_user = _animation_state()
        if (effective, new_user) != (False, False):
            raise Unavailable('Animation write could not be verified; retain snapshot')
    else:
        available, current = _power_state()
        if current != snapshot.previous:
            raise Conflict('Power profile changed since preparation')
        if 'performance' not in available:
            raise Unavailable('Performance profile is no longer advertised')
        if not snapshot.changed:
            return
        _power_command('set', 'performance')
        if _power_state()[1] != 'performance':
            raise Unavailable('Power profile change could not be verified; retain snapshot')


def restore(snapshot):
    """Restore the captured value only if the applied value still appears current."""
    _validate(snapshot)
    if not snapshot.changed:
        return
    if snapshot.setting == ANIMATIONS:
        settings, current, user = _animation_state()
        if (current, user) != (False, False):
            raise Conflict('Animation state changed; refusing to overwrite it')
        try:
            if snapshot.user_value is None:
                settings.reset(_KEY)
            elif not settings.set_boolean(_KEY, snapshot.user_value):
                raise Unavailable('Animation restore was rejected')
        except Unavailable:
            raise
        except Exception as exc:
            raise Unavailable('Animation restore failed') from exc
        _, current, user = _animation_state()
        # An administrator's default may have changed since preparation.
        if user != snapshot.user_value or (snapshot.user_value is not None and current != snapshot.previous):
            raise Unavailable('Animation restore could not be verified')
    else:
        available, current = _power_state()
        if current != 'performance':
            raise Conflict('Power profile changed; refusing to overwrite it')
        if snapshot.previous not in available:
            raise Unavailable('Previous power profile is no longer advertised')
        _power_command('set', snapshot.previous)
        if _power_state()[1] != snapshot.previous:
            raise Unavailable('Power profile restore could not be verified')
