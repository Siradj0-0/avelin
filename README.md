# Avelin

<img src="assets/avelin.svg" alt="Avelin geometric mark" width="80">

A little more clarity for your Linux machine. Avelin is an early-stage, native GTK 4 desktop application for understanding your system and making deliberate changes. It is **not a website**.

> **Early prototype:** not production-ready. There are no published installers or releases yet. Do not rely on Avelin as a backup, a performance guarantee, or a replacement for your system's package manager.

## What works in this first foundation

- Detects Linux distribution, desktop session, CPU, PCI graphics devices (when `lspci` is available), RAM, root filesystem capacity, and active zram swap when readable.
- Dashboard samples CPU and memory every two seconds and shows an in-memory two-minute history. Root storage is capacity used, **not** disk I/O. Unavailable readings appear as unavailable rather than zero.
- A GNOME-only animation toggle reads the live setting and can switch it back. It does not affect non-GNOME desktops.
- A manually confirmed **Empty trash** action calls the system `gio` tool. Deletion is permanent and may include supported mounted volumes. It never runs automatically.
- Checks GitHub for the latest stable `vMAJOR.MINOR.PATCH` release at startup and on request. When a newer version is available, it offers the releases page. **It does not download or install updates.** A check contacts GitHub and exposes normal network metadata such as your IP address to GitHub.
- A source SVG brand mark, open-source license, contribution and security guidelines, unit tests, and CI.

## Run from source

On a Linux desktop, install **Python 3.10+**, **GTK 4**, **PyGObject for GTK 4**, **pycairo**, `gio`, and optionally `pciutils` using your distribution's package manager. Package names differ by distro. Then from the repository root:

```sh
python3 -m avelin
```

Use the distribution Python that has the GI bindings installed. No root is needed to launch the app. The prototype has not yet been tested across all distributions or desktop environments. The desktop file is a development template, not an installer; its module must be installed on Python's import path and its icon registered before deployment.

Tests (standard library only):

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q avelin
```

## Safety and limits

Avelin never silently deletes files or runs privileged commands. Emptying trash is irreversible: inspect it and ensure you have a backup first. It does not scan personal directories, caches, logs, or packages; it does not claim to reclaim a particular amount. Animations are controlled by the existing GNOME user preference, not a system-wide configuration. GPU usage, disk I/O, storage device models, package cleanup, package installation, zram configuration, desktop switching, rollback snapshots, and self-updating are **not implemented**.

A large settings catalog cannot safely be created by multiplying speculative tweaks. Future actions need desktop/distro detection, clear preconditions, impact and risk, preview, explicit confirmation, reversibility or warnings, authentication boundaries, tests, and documented sources. See [research and roadmap](docs/research-and-roadmap.md).

## Distribution and updates

Flatpak, DEB, Arch, AppImage and other builds are planned, not yet available. Sandboxed Flatpak access to host hardware and privileged changes needs a separately designed security model. Native packages should use their distro's update mechanisms; a future AppImage updater needs artifact integrity verification and a reviewed trust model. Until real release assets and those safeguards exist, no self-update will run.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Licensed under [MIT](LICENSE).
