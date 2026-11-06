"""Read-only CPUFreq policy observations, not optimization recommendations.

https://docs.kernel.org/admin-guide/pm/cpufreq.html
CPUFreq policies may cover multiple CPUs and can change during a snapshot.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_POLICY = re.compile(r'policy[0-9]+\Z')


@dataclass(frozen=True)
class CpuPolicy:
    name: str
    governor: str | None
    driver: str | None
    related_cpus: tuple[int, ...] | None


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding='utf-8').strip() or None
    except (OSError, UnicodeError, ValueError):
        return None


def _cpu_list(value: str | None) -> tuple[int, ...] | None:
    if value is None:
        return None
    tokens = value.split()
    if not tokens or any(len(t) > 10 or not t.isascii() or not t.isdigit() for t in tokens):
        return None
    return tuple(int(t) for t in tokens)


def read_cpu_policies(root: str | Path = '/sys/devices/system/cpu/cpufreq') -> tuple[CpuPolicy, ...] | None:
    """None means the policy directory was unavailable; () is a valid empty view.

    Governor can denote a driver-specific scaling algorithm, not necessarily a
    generic governor. Readings are best-effort and not an atomic snapshot.
    """
    try:
        entries = sorted(Path(root).iterdir(), key=lambda p: p.name)
    except (OSError, ValueError):
        return None
    return tuple(CpuPolicy(entry.name, _read(entry / 'scaling_governor'),
                           _read(entry / 'scaling_driver'),
                           _cpu_list(_read(entry / 'related_cpus')))
                 for entry in entries if _POLICY.fullmatch(entry.name))
