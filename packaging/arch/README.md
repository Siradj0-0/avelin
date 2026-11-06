# Experimental Arch package recipe

This is a local, **untested on Arch** recipe, not an official package, AUR submission, release or supported installer. It builds the exact source snapshot `f9fa6a3a69902f1aab9f62a37df953ffa786d4b7`, not the current checkout; changes to the checkout are not included. `0.1.0.r9.gf9fa6a3` identifies that snapshot, not a new upstream release. It retains upstream's internal `0.1.0` version. Update both the snapshot and checksum deliberately for any future recipe change. The SHA-256 checks downloaded bytes against the value in this recipe; it is not a signature or independent proof of provenance. Review the PKGBUILD and source before running them: PKGBUILDs are executable shell code.

**Safety:** This snapshot includes the unfixed power-profile selector. Do not change power profiles through Avelin: a change can cancel another application's hold and switching back will not recreate it. See [issue #15](https://github.com/Siradj0-0/avelin/issues/15). Emptying trash is irreversible. The application may contact GitHub to check releases; it does not install updates. No GTK, screen-reader, desktop, upgrade or distro support is asserted.

## Proposed local build and installation

On a disposable Arch system, install `base-devel` and the recipe's runtime dependencies using your normal, reviewed package-management process. From this directory as an **ordinary user**, with network access:

```sh
makepkg
```

This downloads the pinned GitHub archive, verifies its checksum, stages the files and creates a package in the configured output directory. No `-s` or `-i` is used: missing dependencies fail rather than being installed automatically. Inspect the resulting package and metadata before choosing whether to install it with `pacman -U`. Installation/removal changes the host and typically needs administrator authorization; neither is performed by this recipe's tests. Use a disposable system for initial evaluation.

The package installs a private module and isolated system-Python launcher using the same paths as the experimental Debian package: `/usr/lib/avelin`, `/usr/bin/avelin`, a desktop entry and a hicolor SVG. It uses `avelin-experimental` as the package name but **shares those file paths** with other Avelin packages; do not install alongside another package owning them. Do not force-overwrite package files. `python-gobject` supplies the GI Cairo bridge; `python-cairo` is separately required. `glib2` supplies `gio`. `pciutils` and `power-profiles-daemon` are optional; availability also depends on the system, service and permissions. GNOME settings require compatible schemas and a desktop session. `gio` trash behavior depends on the available desktop/GVfs backend; no complete deletion guarantee is implied.

## Validation still needed

Run `makepkg` as a non-root user in a clean Arch environment; inspect metadata, file ownership/modes, dependencies, desktop entry and icon; install and remove with pacman in a disposable environment; verify `/usr/bin/avelin` from outside the checkout with a GTK display and import `gi`/GTK 4/Cairo using system Python. Exercise upgrades, desktop integration, missing optional services and relevant architectures separately. The mock staging tests in `tests/test_arch_packaging.py` are not makepkg, pacman, GTK or real-Arch integration tests. This recipe has not undergone distribution policy or security review and is not ready for AUR or release.

References: [PKGBUILD(5)](https://man.archlinux.org/man/PKGBUILD.5), [makepkg](https://wiki.archlinux.org/title/Makepkg), [Arch package guidelines](https://wiki.archlinux.org/title/Arch_package_guidelines), [python-gobject and its Cairo option](https://archlinux.org/packages/extra/x86_64/python-gobject/), [python-gobject file list](https://archlinux.org/packages/extra/x86_64/python-gobject/files/), [python-cairo](https://archlinux.org/packages/extra/x86_64/python-cairo/), [GTK 4](https://archlinux.org/packages/extra/x86_64/gtk4/), [glib2 file list](https://archlinux.org/packages/core/x86_64/glib2/files/).
