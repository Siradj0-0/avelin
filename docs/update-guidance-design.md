# Advisory update guidance

This is an experimental backend-only API, not an integrated updater. It does not
inspect the host, determine which installation is running, compare installed
versions, verify artifact provenance, fetch releases, or execute an update.
Nothing here makes an installation automatically updateable. A caller must
provide independently verified installation-origin evidence for the running
copy; no caller is implemented yet. Never treat distribution ID, the presence
of a package manager, a string supplied by an untrusted environment, or a
GitHub release/version match alone as proof of installation ownership.

`update_guidance()` defaults to unknown. Evidence must be a built-in list or
tuple containing at most 64 `InstallOrigin` enum values. A single distinct
recognized origin selects package-managed, Flatpak or source guidance. Unknown,
unrecognized, malformed, oversized, or conflicting evidence yields unknown.
Mappings, sets, generators, other iterators and container subclasses are rejected
without iteration. A caller must surface uncertainty instead of forcing a
choice; duplicate matching evidence does not establish that evidence itself is
trustworthy. An installed local package might not have an update repository
configured. An unrecognized installation method is unknown, not automatically
source or package-managed. The API makes no claim that a newer package exists
or that any remote is trusted. The existing release checker compares numbered
GitHub tags, not installed package versions or channel metadata: an equal tag
does not prove an installed package is current, and a newer tag does not prove
an update exists in its package channel.

No shell commands are returned: a generic `flatpak update` updates all installed
applications and runtimes, which would be broader than updating Avelin. Users
should consult the actual installation's trusted source and official tool
documentation. A checksum next to an untrusted download is not independent
proof of authenticity; package archive verification depends on trusted keys
and configuration.

References:
- https://docs.flatpak.org/en/latest/using-flatpak.html
- https://www.debian.org/doc/manuals/debian-handbook/sect.package-authentication.en.html
- https://docs.github.com/en/actions/concepts/security/artifact-attestations
