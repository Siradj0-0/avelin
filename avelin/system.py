"""Read-only system facts. Unknown values are never represented as zero."""
from __future__ import annotations
import os
import re
import shutil
import subprocess
from pathlib import Path


def read(path: str | Path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except (OSError, ValueError):
        return None


def os_name(path: str = "/etc/os-release") -> str:
    text = read(path) or ""
    for line in text.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.partition("=")[2].strip().strip('"\'')
    return "Linux (distribution unknown)"


def cpu_name() -> str:
    for line in (read('/proc/cpuinfo') or '').splitlines():
        key, sep, value = line.partition(':')
        if sep and key.strip() in ('model name', 'Hardware', 'Processor'):
            return value.strip()
    return 'Unknown CPU'


def graphics() -> list[str]:
    if not shutil.which('lspci'):
        return ['GPU information unavailable (install pciutils)']
    try:
        p = subprocess.run(['lspci'], capture_output=True, text=True, timeout=4, check=True)
        cards = [line.partition(': ')[2].strip() or line for line in p.stdout.splitlines()
                 if re.search(r'VGA compatible controller|3D controller|Display controller', line, re.I)]
        return cards or ['No PCI GPU detected']
    except (OSError, subprocess.SubprocessError):
        return ['GPU information unavailable']


def memory(path: str = '/proc/meminfo') -> tuple[int, int] | None:
    values = {}
    for line in (read(path) or '').splitlines():
        match = re.match(r'^(MemTotal|MemAvailable):\s+(\d+)\s+kB', line)
        if match:
            values[match.group(1)] = int(match.group(2)) * 1024
    total, available = values.get('MemTotal'), values.get('MemAvailable')
    if total is None or available is None or total <= 0:
        return None
    return max(0, total - available), total


def cpu_ticks(path: str = '/proc/stat') -> tuple[int, int] | None:
    try:
        line = (read(path) or '').splitlines()[0].split()
        if line[0] != 'cpu' or len(line) < 5:
            return None
        # Linux reports guest time already included in user/nice; avoid double counting.
        ticks = [int(v) for v in line[1:9]]
        return sum(ticks), ticks[3] + (ticks[4] if len(ticks) > 4 else 0)
    except (ValueError, IndexError):
        return None


def cpu_percent(previous: tuple[int, int] | None, current: tuple[int, int] | None) -> float | None:
    if previous is None or current is None:
        return None
    delta = current[0] - previous[0]
    idle = current[1] - previous[1]
    if delta <= 0 or idle < 0 or idle > delta:
        return None
    return 100 * (delta - idle) / delta


def disk(path: str = '/') -> tuple[int, int] | None:
    try:
        usage = shutil.disk_usage(path)
        return usage.used, usage.total
    except OSError:
        return None


def bytes_label(value: int | None) -> str:
    if value is None:
        return 'Unavailable'
    n = float(value)
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'):
        if abs(n) < 1024 or unit == 'PiB':
            return f'{n:.1f} {unit}' if unit != 'B' else f'{int(n)} B'
        n /= 1024
    return 'Unavailable'


def desktop() -> str:
    return os.environ.get('XDG_CURRENT_DESKTOP') or os.environ.get('DESKTOP_SESSION') or 'Unknown desktop'


def zram_status(path: str = '/proc/swaps') -> str:
    swaps = read(path)
    if swaps is None:
        return 'Unavailable'
    return 'Active' if any('/dev/zram' in line for line in swaps.splitlines()[1:]) else 'Not detected'
