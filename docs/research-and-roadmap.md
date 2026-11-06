# Research and roadmap

## Design

See [DESIGN.md](../DESIGN.md) for the intended interface system and review gates. Research informed the application interface, not just its logo. The visual and accessibility review is still pending.

## Settings research and safety boundaries

| Area | Evidence and future design | State |
| --- | --- | --- |
| GNOME interface | The [GNOME schema](https://github.com/GNOME/gsettings-desktop-schemas/blob/master/schemas/org.gnome.desktop.interface.gschema.xml.in) defines boolean animations, hot corner, clock, battery and cursor options. Detect session and exact key, read and verify changes, and allow switching back. Only animation reduction is potentially performance-related; impact varies. | Seven allowlisted preference toggles |
| zram | [ArchWiki](https://wiki.archlinux.org/title/Zram) describes zram-generator, zswap interaction and lack of hibernation support on zram. Detect existing swap/configuration and package ecosystem, warn about hibernation, back up configuration, and test rollback before offering a change. | Read-only swap detection |
| Desktop replacement | Installing/removing desktops affects login manager, packages, sessions and disk use; it can make the machine hard to log into. Needs per-distro package review, recovery instructions and confirmation. | Not implemented |
| Power profiles | [power-profiles-daemon](https://gitlab.freedesktop.org/upower/power-profiles-daemon) supports profiles on compatible systems; power savings and performance trade off. Detect the service and available profiles; never assume support. [powerprofilesctl](https://manpages.ubuntu.com/manpages/noble/man1/powerprofilesctl.1.html) documents list, get and set. | Optional profile selection with confirmation |
| Startup and background services | [systemctl documentation](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html) distinguishes user and system service management. Disabling unknown services can break networking, login, updates or security. Require scoped catalog, dependencies and rollback. | Research candidate |
| Swap and kernel tuning | [Linux kernel sysctl documentation](https://docs.kernel.org/admin-guide/sysctl/vm.html) describes VM controls. Defaults are not universally bad; unsuitable settings can make workloads worse. Require workload-specific evidence and restore plan. | Research candidate |
| AMD graphics data | The [Linux AMDGPU documentation](https://docs.kernel.org/gpu/amdgpu/driver-misc.html) describes driver-specific sysfs data. Driver files and permissions differ; unavailable readings must stay unavailable. | GPU usage not implemented |

A catalog of thousands of genuine settings requires ongoing distro- and hardware-specific research, integration testing, and safety review; generating thousands of speculative toggles would not satisfy this standard.

## Storage research

[KDE's storage guide](https://linux.kde.org/docs/free-space/) identifies trash, unused Flatpak runtimes, app data and caches as possible sources of space, but caches can be useful and application data may be valuable. [Ubuntu's guidance](https://ubuntu.com/blog/how-to-keep-your-linux-disk-usage-nice-and-tidy-and-save-space) recommends backups and distro-specific package tools. [systemd journalctl](https://www.freedesktop.org/software/systemd/man/journalctl.html) notes that vacuum affects archived logs while disk usage includes active logs. [Flatpak commands](https://docs.flatpak.org/en/latest/flatpak-command-reference.html) distinguish user and system installations.

| Location/action | What to consider before an action | State |
| --- | --- | --- |
| Home trash | Irreversible deletion; other mounts can have separate trash. Preview contents, confirm scope and back up. | Read-only estimate plus explicit gio empty-trash action |
| Application cache | Not all caches are disposable; apps may be open, caches may contain valuable/offline data and rebuilding costs time/bandwidth. | Read-only estimate, no removal |
| APT archives | Only relevant to APT; current settings may disable caching. Cleaning removes cached packages and offline reinstall capability. | Read-only estimate, no removal |
| System journal | Archived logs can contain audit/diagnostic information; vacuum is irreversible and may need privileges. Active logs won't necessarily shrink. | Read-only estimate, no removal |
| Flatpak data/runtimes | Installed app data and runtimes are not interchangeable with junk. Must distinguish user/system installation, preview candidates and verify dependencies. | User data estimate only; no removal |
| Downloads, photos, browser profiles and home files | Not automatically classifiable as trash. | Never scanned or deleted by this version |
| Containers, snapshots, old kernels | Storage may be shared or in use; removal can destroy useful data or recovery capability. Need backend-specific preview and safeguards. | Not implemented |

Storage estimates are bounded, skip descendant symlinks and different-device entries, and mark errors/limits as partial. Initial path prefixes may contain symlinks and same-device bind mounts may be traversed; see [storage safety](storage-safety.md). Allocated-byte estimates can differ from actual recoverable space due to snapshots, compression, shared extents or hard links.

## Distribution, updates and quality

- An experimental [local DEB build path](packaging.md) exists, but no installer is published. Flatpak, Arch and AppImage packages are **not built yet**. [Flatpak](https://docs.flatpak.org/en/latest/repositories.html) and [AppImage](https://docs.appimage.org/packaging-guide/optional/updates.html) use different distribution/update models. Sandbox host access and privileged operations require a separate security model.
- Future update installations must use the package manager or a signed/verifiable, package-specific flow, not blindly execute a GitHub download. The current check is informational only.
- v0.1.0 is a source-only prerelease. v1.0.0 is a future readiness goal, not a guarantee: require real distro/desktop and hardware coverage, package builds, accessibility review, security assessment, recovery tests, documentation and a stable support policy.
- Expand hardware discovery (disks, GPUs and sensors) and support only readings actually available from the system. Track units and sampling intervals.
- Build a narrowly scoped privileged helper only after design and review; never ship a generic root command runner. Every change needs explicit consent, preconditions, rollback/recovery and tests.
