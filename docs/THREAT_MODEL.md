# Threat model

This document describes the repository's current prototype and sets security gates for proposed features. It is not proof of security or a promise that future mechanisms exist. Reassess it when capabilities or release channels change.

## Scope and assets

Avelin is a desktop application running as the invoking user. It reads system and desktop information, can change allowlisted GNOME user settings, can empty the user's trash after confirmation, and checks public GitHub release metadata. Protect user files and settings, availability of the desktop and other applications, integrity of installed software, and the authenticity of information shown to the user. Avoid exposing private system information in public reports; see [SECURITY.md](../SECURITY.md).

## Boundaries and assumptions

- **User session to external tools:** `avelin/actions.py` invokes `gsettings`, `gio`, and `powerprofilesctl` with argument lists rather than a shell. The GNOME schema and setting keys are allowlisted. Executable names are resolved via the inherited `PATH`; an attacker controlling the launch environment can substitute a program running with the app's privileges. Do not run Avelin as root. This is not, by itself, privilege escalation.
- **User intent to destructive action:** Emptying trash is irreversible and may partially complete even if the command fails or times out. Confirmation, warnings and failure behavior are described in [trash-action-safety.md](trash-action-safety.md). Do not infer that a failed operation deleted nothing.
- **Power-profile daemon:** A manual profile change can cancel another application's hold; restoring the previous profile does not recreate that hold. The current `set_power_profile` fails closed rather than changing profiles. A separate check followed by a write cannot eliminate a concurrent-hold race. See [power-profile-safety.md](power-profile-safety.md).
- **Filesystem reads:** Storage scanning is metadata-only, not a secure isolation boundary. Symlinked path prefixes and same-device bind mounts have limitations documented in [storage-safety.md](storage-safety.md). Never treat a scan result alone as authority to delete files.
- **Network to release metadata:** The existing checker is advisory only: it fetches release metadata and opens a fixed releases page; it does not download or install assets. A release notice is not verification of a package. The one-page bound, timeouts, redirects, prerelease semantics and lack of artifact verification are detailed in [update-security.md](update-security.md). Network failures, malformed metadata and rate limits must not be represented as proof that the installation is current.
- **Dependencies and distribution:** The local Debian package is experimental, not a published update channel. Other distribution formats are not established by that package. Use the trusted installation channel and native package-manager verification for managed packages; see [packaging.md](packaging.md) and [APT's archive authentication model](https://manpages.debian.org/trixie/apt/apt-secure.8.en.html).

## Adversaries and limits

Consider untrusted release metadata, hostile or malformed inputs, a compromised network or release account, and a local user who can directly invoke a future privileged interface, influence their own environment, or race filesystem paths. A malicious process already running as the same user can generally act with that user's own permissions; the app must not turn this into access beyond those permissions. A compromised root account, kernel, or trusted package signing key is outside the guarantees of this application, but incident response and key rotation still matter.

## Gates for future privileged operations

There is currently no privileged helper in the inspected main tree. Before adding one:

1. Define fixed, minimal operations and their exact typed arguments; reject unknown operations, extra arguments and out-of-range values inside the privileged mechanism, not just in the UI. Never accept arbitrary commands, shell fragments or caller-selected executable paths.
2. Require explicit user confirmation and appropriate polkit authorization for each operation; a request can reach the helper directly without the GUI. `pkexec` does not validate a program's arguments. Avoid retained authorization for operations whose targets or arguments vary unless its consequences are explicitly designed and reviewed. See [pkexec](https://polkit.pages.freedesktop.org/polkit/pkexec.1.html) and [polkit authorization semantics](https://polkit.pages.freedesktop.org/polkit/polkit.8.html).
3. Use trusted absolute executable paths, a constrained environment and safe imports. Prevent symlink and rename races using descriptor-relative operations and suitable ownership/type checks where files are involved. Design authorization, validation and resource handling together.
4. Offer a dry-run preview; make changes reversible or clearly warn when they are not. Put risky system-wide changes behind explicit Advanced opt-in. Fail closed on missing authorization, ambiguous targets, cancellation or errors.
5. Test direct calls, malformed values, authorization denial, environment substitution, concurrent requests, path races, rollback failures and partial completion in disposable environments. Independent security review is required before integration.

## Gates for future updates

No release artifact is installed by the current checker. Before any direct download or install, specify the trusted publisher and key distribution, verify the exact artifact and origin, address key rotation and downgrade/replay, and fail closed when verification is missing or fails. A checksum retrieved from the same compromised source as the artifact is not independent proof of authenticity. See [GitHub release integrity](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity).

Detect the actual installation method; never replace files managed by a package manager. For any future supported format, require explicit confirmation, format-appropriate verification, a dry-run, and isolated install/upgrade/interruption/rollback tests before enabling the path. An AppImage replacement or privileged `.deb` installation requires its own reviewed threat model; no such implementation is implied here.

## Residual risk and reporting

Tests with mocked commands cannot establish real daemon, desktop, package-manager or polkit behavior. Validate integrations on disposable systems and report missing evidence rather than claiming coverage. Report suspected vulnerabilities privately as directed in [SECURITY.md](../SECURITY.md).
