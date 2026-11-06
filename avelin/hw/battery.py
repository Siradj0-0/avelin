"""Best-effort read-only battery inventory from the process's sysfs view.

Kernel power supply ABI: https://docs.kernel.org/power/power_supply_class.html
A snapshot is not atomic and does not prove that the host has no other devices.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Battery:
    name: str
    present: bool | None
    status: str | None
    capacity_percent: int | None


@dataclass(frozen=True)
class BatteryInventory:
    batteries: tuple[Battery, ...]
    complete: bool


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding='utf-8').strip() or None
    except (OSError, UnicodeError, ValueError):
        return None


def _capacity(text: str | None) -> int | None:
    if text is None or len(text) > 10 or not text.isascii() or not text.isdigit():
        return None
    value = int(text)
    return value if value <= 100 else None


def read_batteries(root: str | Path = '/sys/class/power_supply') -> BatteryInventory | None:
    """Return None when enumeration failed; an empty complete inventory is valid.

    Missing type data makes inventory incomplete. Optional per-battery data use
    None when unavailable. Readings can change during collection.
    """
    try:
        supplies = sorted(Path(root).iterdir(), key=lambda p: p.name)
    except (OSError, ValueError):
        return None
    complete = True
    result = []
    for supply in supplies:
        kind = _read(supply / 'type')
        if kind is None:
            complete = False
            continue
        if kind != 'Battery':
            continue
        raw_present = _read(supply / 'present')
        present = {'0': False, '1': True}.get(raw_present)
        if present is False:
            status, capacity = None, None
        else:
            status = _read(supply / 'status')
            capacity = _capacity(_read(supply / 'capacity'))
        result.append(Battery(supply.name, present, status, capacity))
    return BatteryInventory(tuple(result), complete)
