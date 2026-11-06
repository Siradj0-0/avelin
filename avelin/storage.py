"""Bounded, read-only storage audit. Nothing in this module deletes files."""
from dataclasses import dataclass
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
    """Approximate allocated file bytes without following symlinks or crossing devices.

    Estimates are not reclaimable-space promises: hardlinks, compression, snapshots,
    shared extents and permissions can change actual free space.
    """
    root = Path(path)
    try:
        info = root.lstat()
    except FileNotFoundError:
        return AuditResult(name, str(root), None, 'missing', 'Not present')
    except OSError:
        return AuditResult(name, str(root), None, 'unavailable', 'Cannot read this location')
    if not stat.S_ISDIR(info.st_mode):
        return AuditResult(name, str(root), None, 'unavailable', 'Not a directory; symbolic links are not followed')
    root_dev = info.st_dev
    seen = set()
    stack = []
    total = 0
    count = 0
    incomplete = False
    deadline = time.monotonic() + seconds
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        root_fd = os.open(str(root), flags)
        if os.fstat(root_fd).st_dev != root_dev:
            os.close(root_fd)
            return AuditResult(name, str(root), None, 'unavailable', 'Location changed during scan')
        try:
            stack.append((root_fd, os.scandir(root_fd)))
        except OSError:
            os.close(root_fd)
            raise
        while stack:
            if time.monotonic() >= deadline or count >= max_entries:
                incomplete = True
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
                incomplete = True
                entries.close()
                os.close(parent_fd)
                stack.pop()
                continue
            count += 1
            try:
                entry_info = entry.stat(follow_symlinks=False)
                if entry_info.st_dev != root_dev:
                    incomplete = True
                elif stat.S_ISDIR(entry_info.st_mode):
                    if len(stack) >= 64:
                        incomplete = True
                        continue
                    child_fd = os.open(entry.name, flags, dir_fd=parent_fd)
                    if os.fstat(child_fd).st_dev != root_dev:
                        os.close(child_fd)
                        incomplete = True
                        continue
                    try:
                        child_entries = os.scandir(child_fd)
                    except OSError:
                        os.close(child_fd)
                        raise
                    stack.append((child_fd, child_entries))
                elif stat.S_ISREG(entry_info.st_mode):
                    identity = (entry_info.st_dev, entry_info.st_ino)
                    if identity not in seen:
                        seen.add(identity)
                        total += getattr(entry_info, 'st_blocks', 0) * 512
            except OSError:
                incomplete = True
    except OSError:
        return AuditResult(name, str(root), None, 'unavailable', 'Cannot read this location')
    finally:
        for fd, entries in reversed(stack):
            entries.close()
            os.close(fd)
    status = 'partial' if incomplete else 'complete'
    note = 'Partial: time, entry limit, permissions or another filesystem' if incomplete else 'Estimated allocated file space'
    return AuditResult(name, str(root), total, status, note)


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
