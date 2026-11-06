"""Read-only Linux compressed-swap observations; not a hibernation assessment.

Only known procfs/sysfs attributes are read. In particular, never read
zram-control/hot_add: reading that attribute creates a device.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Swap:
    path: str
    kind: str
    size_bytes: int
    used_bytes: int
    priority: int

    @property
    def is_canonical_zram_path(self) -> bool:
        # Aliases and symlinks cannot safely be identified from this string.
        return bool(re.fullmatch(r'/dev/zram[0-9]+', self.path))


@dataclass(frozen=True)
class ZramDevice:
    name: str
    disksize_bytes: int | None
    algorithm: str | None
    algorithms: tuple[str, ...] | None
    original_bytes: int | None
    compressed_bytes: int | None
    memory_bytes: int | None


@dataclass(frozen=True)
class Diagnostics:
    # None means unavailable or malformed, not an empty list or disabled.
    swaps: tuple[Swap, ...] | None
    devices: tuple[ZramDevice, ...] | None
    zswap_enabled: bool | None
    # Nonempty raw tokens, not a validated list of known sleep states.
    power_states: tuple[str, ...] | None
    resume_device: str | None
    resume_offset: int | None
    issues: tuple[str, ...]


def _read(path: Path, issues: list[str]) -> str | None:
    try:
        # Small known kernel attributes; avoid unbounded input in test roots.
        with path.open('r', encoding='utf-8', errors='strict') as stream:
            text = stream.read(65537)
        if len(text) > 65536:
            raise ValueError('too large')
        return text.strip()
    except (OSError, UnicodeError, ValueError):
        issues.append(f'{path}: unavailable or unreadable')
        return None


def _number(text: str | None, path: Path, issues: list[str]) -> int | None:
    if text is None:
        return None
    if not re.fullmatch(r'[0-9]{1,20}', text):
        issues.append(f'{path}: malformed number')
        return None
    return int(text)


def _swaps(path: Path, issues: list[str]) -> tuple[Swap, ...] | None:
    text = _read(path, issues)
    if text is None:
        return None
    lines = text.splitlines()
    if not lines or lines[0].split() != ['Filename', 'Type', 'Size', 'Used', 'Priority']:
        issues.append(f'{path}: malformed swap header')
        return None
    result = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) != 5 or parts[1] not in ('partition', 'file') or not re.fullmatch(r'[0-9]{1,20}', parts[2]) or not re.fullmatch(r'[0-9]{1,20}', parts[3]) or not re.fullmatch(r'-?[0-9]{1,20}', parts[4]):
            issues.append(f'{path}: malformed swap entry')
            return None
        # Kernel proc paths may encode whitespace/backslashes as octal escapes.
        name = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), parts[0])
        result.append(Swap(name, parts[1], int(parts[2]) * 1024,
                           int(parts[3]) * 1024, int(parts[4])))
    return tuple(result)


def _device(path: Path, issues: list[str]) -> ZramDevice:
    size_path = path / 'disksize'
    size = _number(_read(size_path, issues), size_path, issues)
    algorithm_path = path / 'comp_algorithm'
    raw = _read(algorithm_path, issues)
    selected = None
    algorithms = None
    if raw is not None:
        tokens = raw.split()
        chosen = [token[1:-1] for token in tokens if re.fullmatch(r'\[[^\[\]\s]+\]', token)]
        if tokens and len(chosen) == 1 and all(re.fullmatch(r'[^\[\]\s]+|\[[^\[\]\s]+\]', token) for token in tokens):
            selected = chosen[0]
            algorithms = tuple(token.strip('[]') for token in tokens)
        else:
            issues.append(f'{algorithm_path}: malformed algorithm list')
    stats_path = path / 'mm_stat'
    stats = _read(stats_path, issues)
    values = None
    if stats is not None:
        parts = stats.split()
        if len(parts) >= 3 and all(re.fullmatch(r'[0-9]{1,20}', value) for value in parts):
            values = tuple(int(value) for value in parts[:3])
        else:
            issues.append(f'{stats_path}: malformed memory statistics')
    return ZramDevice(path.name, size, selected, algorithms,
                      *(values if values is not None else (None, None, None)))


def collect(*, proc_root: str | Path = '/proc', sys_root: str | Path = '/sys') -> Diagnostics:
    """Collect best-effort facts without commands, privilege, or host changes.

    Paths may be replaced with fixture roots. Results are not atomic and may
    differ across reads as the system changes. Inspect issues and None values.
    """
    proc, sys = Path(proc_root), Path(sys_root)
    issues: list[str] = []
    swaps = _swaps(proc / 'swaps', issues)
    block = sys / 'block'
    try:
        paths = sorted((p for p in block.iterdir() if re.fullmatch(r'zram[0-9]+', p.name)), key=lambda p: p.name)
        devices = tuple(_device(p, issues) for p in paths)
    except OSError:
        issues.append(f'{block}: cannot enumerate devices')
        devices = None
    enabled_path = sys / 'module/zswap/parameters/enabled'
    raw_enabled = _read(enabled_path, issues)
    enabled = None
    if raw_enabled is not None:
        if raw_enabled.lower() in ('y', '1', 'yes', 'true'):
            enabled = True
        elif raw_enabled.lower() in ('n', '0', 'no', 'false'):
            enabled = False
        else:
            issues.append(f'{enabled_path}: unrecognized enabled value')
    state_path = sys / 'power/state'
    raw_state = _read(state_path, issues)
    states = tuple(raw_state.split()) if raw_state else None
    if raw_state == '':
        issues.append(f'{state_path}: empty power state list')
    resume_path = sys / 'power/resume'
    resume = _read(resume_path, issues)
    if resume is not None and not re.fullmatch(r'[0-9]+:[0-9]+', resume):
        issues.append(f'{resume_path}: malformed resume device')
        resume = None
    offset_path = sys / 'power/resume_offset'
    offset_text = _read(offset_path, issues)
    offset = _number(offset_text, offset_path, issues)
    return Diagnostics(swaps, devices, enabled, states, resume,
                       offset, tuple(issues))
