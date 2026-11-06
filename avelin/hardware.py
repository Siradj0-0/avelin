"""Read-only Linux hardware inventory and carefully scoped utilization.

See docs/hardware-monitoring.md for the API, status semantics and limitations.
"""
from __future__ import annotations

from dataclasses import dataclass
import errno
import math
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
        self._previous: dict[str, tuple[tuple[str, str, str], int, float]] = {}

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

    def _read_at(self, directory: int, relative: str, source: Path, sandbox: bool) -> Reading:
        try:
            fd = os.open(relative, os.O_RDONLY | os.O_CLOEXEC, dir_fd=directory)
            try:
                with os.fdopen(fd, 'r', encoding='utf-8', errors='strict') as stream:
                    fd = -1
                    text = stream.read(4097)
            finally:
                if fd != -1:
                    os.close(fd)
            if len(text) > 4096 or not text.strip():
                return Reading(None, 'invalid', str(source))
            return Reading(text.strip(), 'ok', str(source))
        except OSError as exc:
            return Reading(None, self._error(exc, sandbox), str(source))
        except (UnicodeError, ValueError):
            return Reading(None, 'invalid', str(source))

    @staticmethod
    def _parse_integer(result: Reading, *, minimum: int = 0,
                       maximum: int | None = None, factor: int = 1) -> Reading:
        if result.status != 'ok':
            return result
        text = result.value
        if not isinstance(text, str) or not re.fullmatch(r'[0-9]+', text):
            return Reading(None, 'invalid', result.source)
        try:
            value = int(text)
        except ValueError:
            return Reading(None, 'invalid', result.source)
        if value < minimum or (maximum is not None and value > maximum):
            return Reading(None, 'invalid', result.source)
        return Reading(value * factor, 'ok', result.source)

    def _integer(self, path: Path, sandbox: bool, *, minimum: int = 0,
                 maximum: int | None = None, factor: int = 1) -> Reading:
        return self._parse_integer(self._read(path, sandbox), minimum=minimum,
                                   maximum=maximum, factor=factor)

    def _list(self, path: Path, sandbox: bool) -> tuple[list[Path], str]:
        try:
            return sorted(path.iterdir(), key=lambda p: p.name), 'ok'
        except OSError as exc:
            return [], self._error(exc, sandbox)

    def _busy(self, block: Path, sandbox: bool,
              new: dict[str, tuple[tuple[str, str, str], int, float]]) -> Reading:
        stat_path = block / 'stat'
        try:
            directory = os.open(block, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        except OSError as exc:
            return Reading(None, self._error(exc, sandbox), str(block))
        try:
            try:
                pinned = os.fstat(directory)
                visible = os.stat(block)
            except OSError as exc:
                return Reading(None, self._error(exc, sandbox), str(block))
            token = (pinned.st_dev, pinned.st_ino)
            if token != (visible.st_dev, visible.st_ino):
                return Reading(None, 'unavailable', str(block))

            def read(name: str) -> Reading:
                return self._read_at(directory, name, block / name, sandbox)

            def identity() -> tuple[tuple[str, str] | None, Reading | None]:
                dev = read('dev')
                if dev.status != 'ok':
                    return None, dev
                if not re.fullmatch(r'[0-9]+:[0-9]+', str(dev.value)):
                    return None, Reading(None, 'invalid', dev.source)
                seq = self._parse_integer(read('diskseq'))
                if seq.status != 'ok':
                    return None, seq
                return (str(dev.value), str(seq.value)), None

            before, error = identity()
            if error is not None:
                return error
            accounting = self._parse_integer(read('queue/iostats'), maximum=1)
            if accounting.status != 'ok':
                return accounting
            if accounting.value != 1:
                return Reading(None, 'unavailable', accounting.source)
            stat = read('stat')
            # The observation time belongs to this device's actual counter read,
            # not the beginning of a potentially slow inventory scan.
            observed = self.clock()
            if stat.status != 'ok':
                return stat
            fields = str(stat.value).split()
            if len(fields) < 11 or any(not re.fullmatch(r'[0-9]+', v) for v in fields):
                return Reading(None, 'invalid', str(stat_path))
            try:
                ticks = int(fields[9])
            except ValueError:
                return Reading(None, 'invalid', str(stat_path))
            after, error = identity()
            if error is not None:
                return error
            accounting_after = self._parse_integer(read('queue/iostats'), maximum=1)
            if accounting_after.status != 'ok':
                return accounting_after
            if accounting_after.value != 1:
                return Reading(None, 'unavailable', accounting_after.source)
            try:
                visible_after = os.stat(block)
                pinned_after = os.fstat(directory)
            except OSError as exc:
                return Reading(None, self._error(exc, sandbox), str(block))
            if (before != after or token != (visible_after.st_dev, visible_after.st_ino)
                    or token != (pinned_after.st_dev, pinned_after.st_ino)):
                return Reading(None, 'unavailable', str(block))
            if not math.isfinite(observed):
                return Reading(None, 'invalid', str(stat_path))
            ident = (before[0], f'{token[0]}:{token[1]}', before[1])
            new[block.name] = (ident, ticks, observed)
            previous = self._previous.get(block.name)
            if previous is None or previous[0] != ident:
                return Reading(None, 'warming_up', str(stat_path))
            elapsed = observed - previous[2]
            delta = ticks - previous[1]
            if delta < 0:
                return Reading(None, 'counter_reset', str(stat_path))
            if elapsed <= 0 or delta > elapsed * 1000:
                return Reading(None, 'invalid', str(stat_path))
            return Reading(100.0 * delta / (elapsed * 1000), 'ok', str(stat_path))
        finally:
            os.close(directory)

    def sample(self) -> Snapshot:
        sandbox = self._sandbox()
        now = self.clock()
        blocks, storage_status = self._list(self.sys / 'block', sandbox)
        storage = []
        new: dict[str, tuple[tuple[str, str, str], int, float]] = {}
        for block in blocks:
            # /sys/block lists whole block devices, not individual partitions.
            dev = self._read(block / 'dev', sandbox)
            if dev.status == 'ok' and not re.fullmatch(r'[0-9]+:[0-9]+', str(dev.value)):
                dev = Reading(None, 'invalid', dev.source)
            rotational = self._integer(block / 'queue' / 'rotational', sandbox, maximum=1)
            busy = self._busy(block, sandbox, new)
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
