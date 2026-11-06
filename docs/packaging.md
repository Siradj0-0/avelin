# Experimental Linux packaging

This repository contains a **first, local binary .deb build path**, not a published installer or release asset. It is not yet a Debian source package and has not been submitted to a distribution. The app remains experimental. CI exercises disposable Debian 12 (Bookworm) and Ubuntu 24.04 containers; passing CI is not a promise of support for every derivative, architecture, or desktop. Consult the actual workflow run for results.

## Build and install a local .deb

On a Debian-family system with `python3`, `dpkg-deb` and standard shell/coreutils installed, from a checkout:

```sh
export DEB_MAINTAINER='Your Name <working-email@example.org>'
sh packaging/deb/build.sh
ls dist/deb/
sudo apt install ./dist/deb/avelin_*_all.deb
```

Use an actual reachable maintainer address for a package intended for anyone else; the CI-only address is a non-deliverable placeholder. The script uses the source `__version__` plus `~dev1` so this experimental build sorts before the corresponding release. Only one matching .deb should be present when using the wildcard. Specify a different output directory as the first argument. On installation, APT resolves explicit runtime dependencies: Python 3.10+, PyGObject, its Cairo bridge, pycairo, GTK 4 introspection data and GLib command-line tools. `pciutils` and `power-profiles-daemon` are suggestions for optional features, not prerequisites; availability and permissions still depend on the system. Build on a distro whose packages satisfy those dependencies. No pip or network access is used by the builder.

Launch `avelin` or use the desktop menu. The package installs a private Python module under `/usr/lib/avelin`, an isolated system-Python launcher under `/usr/bin`, a desktop entry and a scalable hicolor icon. Remove it with `sudo apt remove avelin`. The application may contact GitHub to check releases; it does not install updates itself. Inspect the app's safety notes before use.

## Validate in a disposable container

From the checkout, with Docker and network access:

```sh
docker run --rm -v "$PWD:/src:ro" -w /src debian:bookworm sh packaging/deb/test-in-container.sh
docker run --rm -v "$PWD:/src:ro" -w /src ubuntu:24.04 sh packaging/deb/test-in-container.sh
```

The script builds and inspects the package, installs it with APT and dependency resolution, validates the desktop file and icon, smoke-tests the installed GTK window and launcher under Xvfb outside the checkout, and removes the package. It modifies the container and must not be run on a host system. CI performs the same checks and does not publish release assets. These checks do not replace interactive testing on a real desktop, accessibility review, upgrade testing or distribution policy review.

## Other native distribution approaches

- Debian/Ubuntu use `.deb` with dependency metadata; a future distribution submission should use a proper Debian source package and debhelper/dh-python rather than treating this binary-only experiment as archive-ready. See [Debian Policy](https://www.debian.org/doc/debian-policy/ch-binary.html) and [Debian Python Policy](https://www.debian.org/doc/packaging-manuals/python-policy/).
- RPM-family systems normally use an RPM spec and distro-specific dependencies; Arch uses a PKGBUILD. Neither is implemented or tested here.
- Flatpak uses a manifest, runtime and explicitly reviewed sandbox permissions. Avelin reads host system information and invokes desktop/system utilities, so the sandbox implications need design and real-host testing; Flatpak is not implemented here. See [Flatpak conventions](https://docs.flatpak.org/en/latest/conventions.html).
- Desktop integration follows the [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/latest/) and [Icon Theme Specification](https://specifications.freedesktop.org/icon-theme-spec/latest/). Other formats, including AppImage, are not provided by this change.
