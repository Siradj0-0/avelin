# Avelin

<img src="assets/avelin.svg" alt="Avelin geometric mark" width="80">

A little more clarity for your Linux machine. Avelin is an early-stage **native GTK 4 desktop application** for understanding your system and making deliberate changes. It is not a website.

> **v0.1.0 is an experimental, source-only prerelease.** No installers are available. The GTK interface still needs visual, accessibility and real-distro testing. Do not use this as a backup or on a critical machine.

> **Power-profile safety notice:** In the v0.1.0 prerelease, changing the power profile through Avelin can cancel other applications' power-profile holds. Switching back does not restore those holds. Avoid changing power profiles through Avelin until a corrected release is available. See [issue #15](https://github.com/Siradj0-0/avelin/issues/15).

## What's in this preview

- Detects distribution, desktop, CPU, PCI graphics devices (when `lspci` is present), RAM, root filesystem capacity and active zram swap when readable.
- Dashboard samples CPU and RAM every two seconds and graphs an in-memory history; root storage is capacity used, not disk I/O. Unavailable readings are not reported as zero.
- Power-profile discovery when `powerprofilesctl` and its service are available. Changing profiles through Avelin is temporarily disabled: switching can cancel another application’s profile hold, which switching back cannot restore. Selecting the already-current profile does not write a change.
- Seven reversible, allowlisted GNOME user preferences, including animations, hot corner, clock, battery display and cursor blinking. These are not all performance optimizations; unsupported settings are disabled.
- An on-demand, read-only scan estimates allocated space in common cache, home trash, APT archive, system journal and user Flatpak locations. It marks incomplete scans, skips symlink entries and different-device entries, and does not equate size with reclaimable space. Initial path prefixes may contain symlinks and same-device bind mounts may be traversed. It never removes scan results.
- **Empty trash** is a separate, manually confirmed action. It permanently removes trash from locations managed by your desktop, including supported mounted volumes. Check the contents and your backups first.
- Checks up to 30 GitHub releases for numeric `vMAJOR.MINOR.PATCH` tags on startup and on request, including prereleases. If newer, it offers the releases page; it **does not download or install updates**. GitHub can see normal network metadata such as your IP address.
- Source SVG logo, MIT license, contribution and security guidance, research, unit tests and a CI configuration.

## Run from source

On a Linux desktop, install Python 3.10+, GTK 4, PyGObject for GTK 4, the PyGObject Cairo bridge, pycairo, `gio`, and optionally `pciutils` using your distribution's package manager. Package names differ by distro. Then from the repository root:

```sh
python3 -m avelin
```

Use your distribution Python with GI bindings. No root is needed. The included desktop file is a development template, not an installer; its module must be installed on Python's import path and icon registered before deployment. For a Debian/Ubuntu source setup example and troubleshooting, see [running from source](docs/source-setup.md).

Run tests:

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q avelin
```

## Safety and limits

Avelin never silently deletes files or runs privileged commands. Emptying trash is irreversible; inspect it and back up first. The storage scan is not a cleanup recommendation and may be partial. Package caches, logs, app data, personal files and Flatpak data are **not deleted**. GPU usage, disk I/O, disk models, privileged optimization, package installation, zram changes, desktop switching, rollback snapshots and self-updating are **not implemented**.

An experimental local DEB build path is available; no installer has been published. Flatpak, Arch, AppImage and other packages remain planned. See [packaging documentation](docs/packaging.md). See [research and roadmap](docs/research-and-roadmap.md) and [design direction](DESIGN.md). A future v1.0.0 is the goal for production readiness, but no software can guarantee it will work on every machine.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Licensed under [MIT](LICENSE).
