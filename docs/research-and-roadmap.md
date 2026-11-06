# Research and roadmap

## Design direction

Quiet dark surfaces, compact navigation, generous spacing, readable labels, and real device data over decorative metrics. Error and unsupported states are explicit. The mark is an original geometric SVG, not a vendor logo.

Design research: [Impeccable](https://github.com/pbakaus/impeccable) provides critique, accessibility audit, hardening and anti-generic design guidance; [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) emphasizes distinctive interfaces; [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/) inform native interaction. These are references, not installed dependencies. Native GTK behavior and accessibility take precedence over web-specific patterns.

## Research findings

- [Ubuntu's storage cleanup guidance](https://ubuntu.com/blog/how-to-keep-your-linux-disk-usage-nice-and-tidy-and-save-space) recommends backups before removal and notes distro-specific package-cache tools. Avoid indiscriminate cache and user-file deletion.
- [ArchWiki's zram guide](https://wiki.archlinux.org/title/Zram) describes compressed swap and notes hibernation and zswap interactions. Installing/configuring zram requires distribution-specific conflict detection and recovery; the current build only detects active zram swap.
- [Flatpak's command reference](https://docs.flatpak.org/en/latest/flatpak-command-reference.html) and [AppImage update documentation](https://docs.appimage.org/packaging-guide/optional/updates.html) support package-specific update approaches. Downloading and executing an arbitrary latest release is not a safe universal updater.

## Planned, not implemented

1. Test the GTK interface and accessibility with real GNOME, KDE, Xfce and older hardware; add keyboard and screen-reader review.
2. Storage audit: inspect known cache/log sizes, identify ownership, explain effects, preview specific items, support separate opt-in actions and verify outcome. Never silently delete downloads, browser profiles, package-manager state, or personal files. Require additional confirmation for irreversible operations.
3. Capability-based settings registry: each action has detection, source, risk, affected scope, current state, preconditions, proposed change, verification and rollback/recovery instructions. Introduce tested settings incrementally, not thousands of unverified toggles.
4. Privileged helper: narrow allowlisted operations and policy-based authorization, no generic command runner. Review security and create a recovery strategy before adding package installation, zram changes or desktop replacement.
5. Hardware: discover storage devices, GPU/iGPU usage where supported, sensors and per-device history. Clearly label missing data and measurement units.
6. Build and test Flatpak, DEB, Arch and AppImage packages, then publish signed or verifiable release artifacts. Implement update handling per installation method with authenticity verification; handle source installs without self-modification.
7. Add UI integration tests, distro/desktop matrix, translations, documentation, issue templates, and actual release procedures.
