"""Discover hwmon temperature channels without assuming their location or unit.

Some hwmon temp inputs are millivolts, not millidegrees Celsius. This module
returns raw integers, not temperature values: see
https://docs.kernel.org/hwmon/sysfs-interface.html. Readings are not atomic.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_CHANNEL = re.compile(r'temp([1-9][0-9]*)_input\Z')
_INTEGER = re.compile(r'-?[0-9]+\Z')


@dataclass(frozen=True)
class ThermalChannel:
    device: str
    chip_name: str | None
    channel: int
    label: str | None
    raw_input: int | None


@dataclass(frozen=True)
class ThermalInventory:
    channels: tuple[ThermalChannel, ...]
    complete: bool


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding='utf-8').strip() or None
    except (OSError, UnicodeError, ValueError):
        return None


def _raw_integer(value: str | None) -> int | None:
    if value is None or len(value) > 20 or not _INTEGER.fullmatch(value):
        return None
    return int(value)


def read_thermal_channels(root: str | Path = '/sys/class/hwmon') -> ThermalInventory | None:
    """Return None for unavailable enumeration, and a possibly incomplete snapshot.

    raw_input is unit-ambiguous and must not be presented as degrees Celsius.
    Neither labels nor indices establish which component a sensor monitors.
    """
    try:
        devices = sorted(Path(root).iterdir(), key=lambda p: p.name)
    except (OSError, ValueError):
        return None
    complete = True
    channels = []
    for device in devices:
        try:
            entries = sorted(device.iterdir(), key=lambda p: p.name)
        except (OSError, ValueError):
            complete = False
            continue
        chip = _read(device / 'name')
        for entry in entries:
            match = _CHANNEL.fullmatch(entry.name)
            if match is None:
                continue
            number = match.group(1)
            channels.append(ThermalChannel(device.name, chip, int(number),
                                           _read(device / f'temp{number}_label'),
                                           _raw_integer(_read(entry))))
    return ThermalInventory(tuple(channels), complete)
