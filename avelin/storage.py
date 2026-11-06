"""Bounded, read-only storage audit. Nothing in this module deletes files."""
from dataclasses import dataclass
import math
import os
from pathlib import Path
import stat
import time


@dataclass(frozen=True)
class AuditResult:
    name: str
    path: str
    allocated_bytes: int | None
    status: str
    note: str


def measure(name: str, path: str | Path, *, max_entries: int = 100_000, seconds: float = 3.0) -> AuditResult:
    """Estimate regular-file allocated bytes, without opening file contents.

    This is not a snapshot or a reclaimable-space estimate. Partial results contain
    only the known subtotal. Directory and symlink allocation is excluded.
    """
    if not isinstance(max_entries, int) or isinstance(max_entries, bool) or max_entries < 0:
        raise ValueError('max_entries must be a non-negative integer')
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('seconds must be a finite non-negative number')
    root = Path(path)
    try:
        info = root.lstat()
    except FileNotFoundError:
        return AuditResult(name, str(root), None, 'missing', 'Not present')
    except OSError:
        return AuditResult(name, str(root), None, 'unavailable', 'Cannot read this location')
    if not stat.S_ISDIR(info.st_mode):
        return AuditResult(name, str(root), None, 'unavailable', 'Not a directory; symbolic links are not followed')

    # These descriptor-relative APIs are required for safe traversal. Do not
    # silently downgrade to a path-based walk on unsupported platforms.
    if not all(hasattr(os, flag) for flag in ('O_DIRECTORY', 'O_NOFOLLOW', 'O_CLOEXEC')):
        return AuditResult(name, str(root), None, 'unavailable', 'Safe directory scanning is unsupported')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    root_dev = info.st_dev
    seen_files = set()
    seen_dirs = {(info.st_dev, info.st_ino)}
    stack = []
    reasons = set()
    total = 0
    count = 0
    deadline = time.monotonic() + seconds

    def open_directory(path, expected, parent_fd=None):
        fd = os.open(path, flags, dir_fd=parent_fd)
        try:
            actual = os.fstat(fd)
            if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
                return None
            entries = os.scandir(fd)
            stack.append((fd, entries))
            fd = None  # stack owns it now
            return actual
        finally:
            if fd is not None:
                os.close(fd)

    try:
        try:
            opened = open_directory(str(root), info)
        except (OSError, NotImplementedError):
            return AuditResult(name, str(root), None, 'unavailable', 'Cannot safely read this location')
        if opened is None:
            return AuditResult(name, str(root), None, 'unavailable', 'Location changed during scan')
        while stack:
            if time.monotonic() >= deadline:
                reasons.add('time limit')
                break
            parent_fd, entries = stack[-1]
            try:
                entry = next(entries)
            except StopIteration:
                entries.close()
                os.close(parent_fd)
                stack.pop()
                continue
            except OSError:
                reasons.add('directory read error')
                entries.close()
                os.close(parent_fd)
                stack.pop()
                continue
            # Probe for a further entry before declaring a limit, so exactly N
            # entries can be scanned completely with max_entries=N.
            if count >= max_entries:
                reasons.add('entry limit')
                break
            count += 1
            try:
                entry_info = os.stat(entry.name, dir_fd=parent_fd, follow_symlinks=False)
                if stat.S_ISLNK(entry_info.st_mode):
                    continue
                if entry_info.st_dev != root_dev:
                    reasons.add('other filesystem')
                elif stat.S_ISDIR(entry_info.st_mode):
                    identity = (entry_info.st_dev, entry_info.st_ino)
                    if identity in seen_dirs:
                        reasons.add('repeated directory')
                        continue
                    if len(stack) >= 64:
                        reasons.add('depth limit')
                        continue
                    actual = open_directory(entry.name, entry_info, parent_fd)
                    if actual is None:
                        reasons.add('directory changed')
                    else:
                        seen_dirs.add(identity)
                elif stat.S_ISREG(entry_info.st_mode):
                    identity = (entry_info.st_dev, entry_info.st_ino)
                    if identity not in seen_files:
                        seen_files.add(identity)
                        blocks = getattr(entry_info, 'st_blocks', None)
                        if blocks is None or blocks < 0:
                            reasons.add('allocated size unavailable')
                        else:
                            total += blocks * 512
            except (OSError, NotImplementedError):
                reasons.add('access or filesystem error')
    finally:
        for fd, entries in reversed(stack):
            entries.close()
            os.close(fd)
    if reasons:
        return AuditResult(name, str(root), total, 'partial', 'Partial subtotal: ' + ', '.join(sorted(reasons)))
    return AuditResult(name, str(root), total, 'complete', 'Estimated allocated regular-file space')


def locations() -> list[tuple[str, Path]]:
    home = Path.home()
    cache = Path(os.environ.get('XDG_CACHE_HOME') or home / '.cache')
    data = Path(os.environ.get('XDG_DATA_HOME') or home / '.local/share')
    # Freedesktop base directory paths must be absolute; ignore malformed values.
    if not cache.is_absolute():
        cache = home / '.cache'
    if not data.is_absolute():
        data = home / '.local/share'
    return [
        ('Application caches', cache),
        ('Home trash', data / 'Trash/files'),
        ('APT package archives', Path('/var/cache/apt/archives')),
        ('System journal files', Path('/var/log/journal')),
        ('User Flatpak data', data / 'flatpak'),
    ]


def scan() -> list[AuditResult]:
    return [measure(name, path) for name, path in locations()]
