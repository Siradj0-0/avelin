# Compressed-swap diagnostics: research and design

This is a standalone, unintegrated, **read-only** prototype. It does not install packages, load kernel modules, configure swap or hibernation, change sysfs, restart services, use elevated privileges, or assess whether hibernation will succeed. It has no GUI, automatic execution, or recommendations to change the machine.

## Background

- [Linux zram documentation](https://docs.kernel.org/6.12/admin-guide/blockdev/zram.html): zram provides compressed RAM-backed block devices for swap or other purposes. `disksize` is logical capacity, not actual RAM consumption; `mm_stat` exposes original bytes, compressed bytes, and allocated memory including overhead. The selected algorithm is bracketed. **Reading** `zram-control/hot_add` creates a device, so a read-only probe must never read it.
- [Linux zswap documentation](https://www.kernel.org/doc/html/latest/admin-guide/mm/zswap.html): zswap is a compressed cache for swap, distinct from zram, and can evict to a backing swap device. Runtime `enabled` reflects whether it accepts new pages; disabling it does not immediately empty its pool. A missing parameter does not prove it is disabled or unsupported.
- [Linux software suspend documentation](https://docs.kernel.org/5.16/power/swsusp.html) describes resume device selection and the additional offset needed for swap files. The [Fedora SwapOnZRAM change](https://fedoraproject.org/wiki/Changes/SwapOnZRAM) describes how zram and disk swap may coexist and the complications for hibernation. RAM-backed zram is not persistent hibernation storage. A disk-backed swap entry, `disk` in `/sys/power/state`, or a nonzero resume device alone cannot establish hibernation readiness; image sizing, resume mapping, initramfs, firmware, encryption, filesystem, security policy and systemd configuration also matter.
- Distro configuration is not uniform: [Fedora's change](https://fedoraproject.org/wiki/Changes/SwapOnZRAM) describes `zram-generator-defaults`; [Fedora CoreOS documentation](https://docs.fedoraproject.org/en-US/fedora-coreos/sysconfig-configure-swaponzram/) notes its different default. [Debian's zram wiki](https://wiki.debian.org/ZRam) lists `zram-tools` and `systemd-zram-generator`. The [upstream generator](https://github.com/systemd/zram-generator) searches configuration in `/run`, `/etc`, `/usr/local/lib`, and `/usr/lib`, and also applies drop-ins. A file or tool's presence alone does not prove effective configuration or ownership. No distribution tooling is invoked or changed here.

## Prototype contract

`avelin.zram_info.collect()` reads only `/proc/swaps`, the names under `/sys/block`, and explicitly listed kernel attributes under each `/sys/block/zramN`, `/sys/module/zswap/parameters/enabled`, and `/sys/power`. Optional `proc_root` and `sys_root` parameters support fixture tests, not untrusted arbitrary roots. It runs no commands and never scans the zram-control directory. Reads may still race device removal or kernel changes, and snapshots are not atomic.

`Diagnostics` reports active swap entries (sizes and usage converted from KiB to bytes, plus priority), zram devices and their logical size, selected/available compression algorithms and the first three `mm_stat` byte counters, zswap's runtime enable flag, supported power-state tokens, and raw resume major:minor plus integer offset. `Swap.is_canonical_zram_path` matches only literal `/dev/zramN` paths: false is **not** proof of non-zram, as symlink or other aliases are not resolved. Device enumeration is separate from swap, since zram can be used for other purposes. No correlation or hibernation verdict is inferred.

`None` means unknown, unavailable, or malformed; empty tuples mean a readable empty list. Zero is preserved. Each failed or malformed source adds an issue; incomplete devices retain whatever was readable. A malformed swaps table makes the entire swap list unknown rather than silently omitting entries. A missing zram directory, zswap parameter, power file, or optional statistic may reflect kernel configuration, permissions, containers, or another environment; it is not a negative capability assertion. Values and paths can reveal system details: future UIs or logs must avoid exposing them without user intent.

## Integration prerequisites and unknowns

- Agree on user-facing terminology, explicit unknown/partial presentation and privacy; don't interpret absent data as disabled or empty. Reconcile the existing `system.zram_status()` before exposing another status. Neither is authoritative about aliases.
- Test on representative kernels and distributions (including zram absent, multiple devices, zswap enabled/disabled, non-swap zram, aliases, containers, unreadable sysfs and device churn). Fixture tests are not real-hardware validation; no distro coverage or hibernation test is claimed.
- Establish UI threading and refresh bounds; proc/sys reads can change between observations. The prototype makes no claim of bounded filesystem latency.
- Any future hibernation readiness check needs a separately reviewed design covering actual resume target resolution, file offsets, adequate persistent swap, systemd and initramfs behavior, encryption, firmware/security policy, permissions, and distro differences. Showing a candidate is not proof that hibernation is safe or works. No configuration or action is authorized by this diagnostic.
- If future work considers settings or package management, obtain explicit user approval, separately review reversibility and privileged operations, and never treat this module as authorization to make changes.

## Tests

Run `python3 -m unittest discover -s tests -v` on Python 3.10+. Fixtures cover empty, multiple, malformed and missing data, permission failure, units, alias handling, and guarding the dangerous `hot_add` path. These tests do not install software, exercise hibernation or make host changes.
