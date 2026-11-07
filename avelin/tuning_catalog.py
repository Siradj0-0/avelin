"""Static, informational context about selected Linux settings.

This module never detects, recommends, applies, or restores a setting. An entry's
presence does not imply that the host supports it or that Avelin implements it.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TuningInfo:
    id: str
    title: str
    scope: str
    prerequisites: str
    reversibility: str
    risks: str
    avelin_status: str
    source_urls: tuple[str, ...]


_CATALOG = (
    TuningInfo(
        id='gnome-animations',
        title='GNOME desktop animations',
        scope='GNOME desktop interface preference for the current user',
        prerequisites=('A compatible desktop, the relevant GNOME interface schema '
                       'and a writable user setting; applicability is not assessed.'),
        reversibility=('The preference may be changed back if writable. Restoring '
                       'the exact prior state requires knowing whether a user '
                       'override existed and preserving its value.'),
        risks=('Changing visual motion affects the interface and accessibility; '
               'behavior varies across desktop components. No speedup is promised.'),
        avelin_status=('Some versions expose a GNOME animation preference. This '
                       'catalog does not inspect or operate that control.'),
        source_urls=(
            'https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/raw/main/schemas/org.gnome.desktop.interface.gschema.xml.in',
            'https://docs.gtk.org/gio/method.Settings.get_user_value.html',
            'https://docs.gtk.org/gio/method.Settings.reset.html',
        ),
    ),
    TuningInfo(
        id='compressed-swap',
        title='zram compressed RAM-backed block devices',
        scope='Kernel block device; can be used as swap or for other purposes',
        prerequisites=('A kernel with zram support and appropriate configuration, '
                       'which varies by distribution or setup; swap and hibernation need '
                       'independent verification. Applicability is not assessed.'),
        reversibility=('Restoring configuration does not recreate the previous '
                       'device state or data; safe removal and recovery depend '
                       'on how the device is used.'),
        risks=('Compression uses CPU and memory; consequences depend on workload '
               'and configuration. Reset frees stored data. Do not infer '
               'hibernation readiness from a zram observation alone.'),
        avelin_status=('Some versions report swap information. This catalog '
                       'does not configure, inspect, or reset zram.'),
        source_urls=(
            'https://docs.kernel.org/admin-guide/blockdev/zram.html',
            'https://docs.kernel.org/power/swsusp-and-swap-files.html',
        ),
    ),
    TuningInfo(
        id='power-profiles',
        title='System power profiles',
        scope='System-wide profile managed by the power-profiles daemon',
        prerequisites=('A supported service and profile, authorization, and '
                       'compatible hardware; applicability is not assessed.'),
        reversibility=('Changing back cannot recreate another application\'s '
                       'profile hold that a manual change released. Checking '
                       'holds beforehand cannot eliminate the race.'),
        risks=('Profile changes may release other applications\' holds. Power, '
               'heat and battery tradeoffs depend on the machine and workload; '
               'no speedup is promised.'),
        avelin_status=('Power-profile changes have a known safety issue in the '
                       'v0.1.0 prerelease. Do not change profiles through that '
                       'version; see issue #15.'),
        source_urls=(
            'https://upower.pages.freedesktop.org/power-profiles-daemon/gdbus-org.freedesktop.UPower.PowerProfiles.html',
            'https://github.com/Siradj0-0/avelin/issues/15',
        ),
    ),
)


def catalog() -> tuple[TuningInfo, ...]:
    """Return immutable static entries; no host capabilities are checked."""
    return _CATALOG
