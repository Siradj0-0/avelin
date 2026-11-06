# Storage audit: safety and interpretation

## Scope

The scanner is on demand and read-only: it enumerates directories and reads filesystem metadata, but does not open regular-file contents, change permissions, delete files, invoke cleanup commands, or request elevated privileges. A directory read may update filesystem access times, trigger automounts or involve remote filesystem activity; this is not a zero-I/O or metadata-side-effect-free operation. It scans common XDG cache, home trash, APT archives, system journal, and user Flatpak data locations. Flatpak and other application data can be important, not disposable. Paths come from the current user environment and invalid relative XDG paths fall back to standard defaults.

The separate, existing **Empty trash** action in the application is manually confirmed and can permanently delete desktop-managed trash, including on supported mounted volumes. This work does not implement or modify cleanup, recommendations, preview, recovery, or trash deletion. No cleanup of caches, packages, logs, or app data is implemented by this scanner; no deletion should be inferred from its results.

## Reading a result

- `allocated_bytes` is a sum of `st_blocks * 512` for regular files encountered on Linux, not apparent file length and **not reclaimable space**. A sparse file can have a large length but few allocated blocks. Directories, symbolic links and special files contribute no bytes.
- Hard links with the same device and inode are counted once per location, not globally. Location results can overlap or share hard links, so do not sum them as a deduplicated total. A file may also have hard links outside the scanned tree. Compression, reflinks, shared extents, snapshots, filesystem metadata and open-but-deleted files can make these values differ from `du`, filesystem occupancy or actual space freed by deletion.
- `complete` means traversal finished under the stated rules, not that every byte of the filesystem was measured. `partial` is the known subtotal and the note identifies one or more observed limits/errors; it is not a reliable reclaimable-space estimate. When allocated block information is unavailable, affected files are omitted and marked partial rather than silently counted as zero. `missing` and `unavailable` have no numeric total.
- Each location gets at most 100,000 entries, three seconds and 64 open directory levels by default. The count includes all encountered entries, even skipped links and special files. The time limit is checked between operations, not a hard timeout: a stalled filesystem call can take longer. Traversal order is filesystem-dependent, so partial subtotals may vary.

## Boundaries and limitations

Root and child directory final components are not followed if they are symbolic links; descendants are opened relative to already-open directory descriptors using `O_NOFOLLOW` and checked against their device and inode before enumeration. Prefix components of the initial root path may still be symlinks. Separate-device entries are skipped and mark the result partial, but device IDs cannot detect all mount boundaries: same-device bind mounts may be traversed, including outside the intended subtree. Repeated directory identities are skipped and marked partial to prevent loops. These safeguards do not make the scan an isolation or security boundary.

The tree can change during scanning; even with directory identity checks this is not a consistent snapshot. File metadata can become stale or be replaced between operations. Permission errors, disappearing entries, depth, time and entry limits, unsupported block data, and different-device mounts yield partial results. A failed root open or changed root identity yields unavailable. Platform support requires the Linux/POSIX descriptor-relative directory APIs and allocation semantics; the app targets Linux. Scan results depend on the current user's permissions and must not be interpreted as an inventory of all files.

## Sources

- [Python `os` documentation](https://docs.python.org/3/library/os.html#os.scandir) — directory iteration, descriptor and stat interfaces.
- [Linux `stat(2)`](https://man7.org/linux/man-pages/man2/stat.2.html) and [inode(7)](https://man7.org/linux/man-pages/man7/inode.7.html) — inode identity, allocated blocks and portability caveats.
- [Linux `open(2)`](https://man7.org/linux/man-pages/man2/open.2.html) — `O_NOFOLLOW` applies to the final component and descriptor-relative operations.
- [GNU `du` manual](https://www.gnu.org/software/coreutils/manual/html_node/du-invocation.html) — apparent versus allocated usage and hard-link counting.
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/) — defaults and absolute path requirements.
