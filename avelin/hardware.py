"""Read-only Linux hardware inventory and carefully scoped utilization.

See docs/hardware-monitoring.md for the API, status semantics and limitations.
"""
from __future__ import annotations

from dataclasses import dataclass
import errno
import os
from pathlib import Path
import re
import time
from typing import Callable, Mapping


@dataclass(frozen=True)
class Reading:
    value: object | None
    status: str  # ok, unavailable, permission, sandbox, invalid, warming_up, counter_reset
    source: str


@dataclass(frozen=True)
class StorageDevice:
    name: str
    device_number: Reading
    model: Reading
    size_bytes: Reading
    rotational: Reading
    busy_percent: Reading


@dataclass(frozen=True)
class GPUDevice:
    name: str
    vendor_id: Reading
    device_id: Reading
    driver: Reading
    # Portable sysfs does not reliably label every GPU integrated or discrete.
    kind: Reading
    busy_percent: Reading


@dataclass(frozen=True)
class Snapshot:
    storage: tuple[StorageDevice, ...]
    gpus: tuple[GPUDevice, ...]
    storage_status: str
    gpu_status: str
    sandbox: bool
    timestamp: float


class HardwareMonitor:
    """Sample visible devices. Roots, environment and clock are injectable for tests.

    Keep one instance across samples to obtain storage busy percentages. Instances
    are not thread-safe; a caller should serialize sample() calls.
    """

    def __init__(self, sys_root: str | Path = '/sys', proc_root: str | Path = '/proc',
                 root: str | Path = '/', environ: Mapping[str, str] | None = None,
                 clock: Callable[[], float] = time.monotonic):
        self.sys = Path(sys_root)
        self.proc = Path(proc_root)  # reserved for future documented proc interfaces
        self.root = Path(root)
        self.env = os.environ if environ is None else environ
        self.clock = clock
        self._previous: dict[str, tuple[tuple[str, str, str | None], int, float]] = {}

    def _sandbox(self) -> bool:
        # Positive signals only: absence of a marker cannot prove host visibility.
        return bool(self.env.get('FLATPAK_ID') or self.env.get('SNAP') or
                    (self.root / '.flatpak-info').is_file())

    @staticmethod
    def _error(exc: OSError, sandbox: bool) -> str:
        if exc.errno in (errno.EACCES, errno.EPERM):
            return 'permission'
        if exc.errno in (errno.ENOENT, errno.ENOTDIR) and sandbox:
            return 'sandbox'
        return 'unavailable'

    def _read(self, path: Path, sandbox: bool) -> Reading:
        try:
            # sysfs attributes are small; cap untrusted or malformed fixture files.
            with path.open('r', encoding='utf-8', errors='strict') as stream:
                text = stream.read(4097)
            if len(text) > 4096 or not text.strip():
                return Reading(None, 'invalid', str(path))
            return Reading(text.strip(), 'ok', str(path))
        except OSError as exc:
            return Reading(None, self._error(exc, sandbox), str(path))
        except (UnicodeError, ValueError):
            return Reading(None, 'invalid', str(path))

    def _integer(self, path: Path, sandbox: bool, *, minimum: int = 0,
                 maximum: int | None = None, factor: int = 1) -> Reading:
        result = self._read(path, sandbox)
        if result.status != 'ok':
            return result
        text = result.value
        if not isinstance(text, str) or not re.fullmatch(r'[0-9]+', text):
            return Reading(None, 'invalid', str(path))
        try:
            value = int(text)
        except ValueError:
            return Reading(None, 'invalid', str(path))
        if value < minimum or (maximum is not None and value > maximum):
            return Reading(None, 'invalid', str(path))
        return Reading(value * factor, 'ok', str(path))

    def _list(self, path: Path, sandbox: bool) -> tuple[list[Path], str]:
        try:
            return sorted(path.iterdir(), key=lambda p: p.name), 'ok'
        except OSError as exc:
            return [], self._error(exc, sandbox)

    def _busy(self, path: Path, key: str, identity: tuple[str, str, str | None] | None,
              now: float, sandbox: bool,
              new: dict[str, tuple[tuple[str, str, str | None], int, float]]) -> Reading:
        result = self._read(path, sandbox)
        if result.status != 'ok':
            return result
        fields = str(result.value).split()
        if len(fields) < 11 or any(not re.fullmatch(r'[0-9]+', v) for v in fields):
            return Reading(None, 'invalid', str(path))
        try:
            ticks = int(fields[9])
        except ValueError:
            return Reading(None, 'invalid', str(path))
        if identity is None:
            return Reading(None, 'unavailable', str(path))
        new[key] = (identity, ticks, now)
        previous = self._previous.get(key)
        if previous is None or previous[0] != identity:
            return Reading(None, 'warming_up', str(path))
        elapsed = now - previous[2]
        delta = ticks - previous[1]
        if delta < 0:
            return Reading(None, 'counter_reset', str(path))
        if elapsed <= 0 or delta > elapsed * 1000:
            return Reading(None, 'invalid', str(path))
        return Reading(100.0 * delta / (elapsed * 1000), 'ok', str(path))

    def sample(self) -> Snapshot:
        sandbox = self._sandbox()
        now = self.clock()
        blocks, storage_status = self._list(self.sys / 'block', sandbox)
        storage = []
        new: dict[str, tuple[tuple[str, str, str | None], int, float]] = {}
        for block in blocks:
            # /sys/block lists whole block devices, not individual partitions.
            dev = self._read(block / 'dev', sandbox)
            if dev.status == 'ok' and not re.fullmatch(r'[0-9]+:[0-9]+', str(dev.value)):
                dev = Reading(None, 'invalid', dev.source)
            diskseq = self._integer(block / 'diskseq', sandbox)
            try:
                real_path = str(block.resolve(strict=True))
            except (OSError, RuntimeError):
                real_path = ''
            identity = ((str(dev.value), real_path,
                         str(diskseq.value) if diskseq.status == 'ok' else None)
                        if dev.status == 'ok' and real_path else None)
            rotational = self._integer(block / 'queue' / 'rotational', sandbox, maximum=1)
            accounting = self._integer(block / 'queue' / 'iostats', sandbox, maximum=1)
            if accounting.status != 'ok':
                busy = Reading(None, accounting.status, accounting.source)
            elif accounting.value != 1:
                busy = Reading(None, 'unavailable', accounting.source)
            else:
                busy = self._busy(block / 'stat', block.name, identity, now, sandbox, new)
            storage.append(StorageDevice(
                block.name, dev, self._read(block / 'device' / 'model', sandbox),
                self._integer(block / 'size', sandbox, factor=512), rotational,
                busy))
        # Inaccessible listings must not bridge gaps with a stale sample.
        self._previous = new

        cards, gpu_status = self._list(self.sys / 'class' / 'drm', sandbox)
        gpus = []
        seen = set()
        for card in cards:
            if not re.fullmatch(r'card[0-9]+', card.name):
                continue  # connectors and render nodes are not additional GPUs
            device = card / 'device'
            try:
                real = device.resolve(strict=True)
            except OSError as exc:
                # A disappearing/inaccessible device is not proof of an empty inventory.
                status = self._error(exc, sandbox)
                if gpu_status != 'permission' or status == 'permission':
                    gpu_status = status
                continue
            except RuntimeError:
                if gpu_status == 'ok':
                    gpu_status = 'invalid'
                continue
            if real in seen:
                continue
            seen.add(real)
            driver_path = device / 'driver'
            try:
                driver = Reading(driver_path.resolve(strict=True).name, 'ok', str(driver_path))
            except OSError as exc:
                driver = Reading(None, self._error(exc, sandbox), str(driver_path))
            except RuntimeError:
                driver = Reading(None, 'invalid', str(driver_path))
            kind = Reading(None, 'unavailable', str(device))
            busy_path = device / 'gpu_busy_percent'
            # Only the amdgpu ABI is supported; similarly named files from other
            # drivers must not be assumed to mean the same thing.
            if driver.status == 'ok' and driver.value == 'amdgpu':
                busy = self._integer(busy_path, sandbox, maximum=100)
            else:
                busy = Reading(None, driver.status if driver.status != 'ok' else 'unavailable', str(busy_path))
            gpus.append(GPUDevice(card.name, self._read(device / 'vendor', sandbox),
                                  self._read(device / 'device', sandbox), driver, kind, busy))
        return Snapshot(tuple(storage), tuple(gpus), storage_status, gpu_status, sandbox, now)
