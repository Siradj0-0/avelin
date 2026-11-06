"""Passive, advisory update guidance; this module does not inspect or update a system.

Callers must only provide installation evidence they have verified separately. The
classification is not a proof of package ownership or artifact authenticity.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class InstallOrigin(Enum):
    PACKAGE = 'package'
    FLATPAK = 'flatpak'
    SOURCE = 'source'
    UNKNOWN = 'unknown'


@dataclass(frozen=True)
class Guidance:
    origin: InstallOrigin
    message: str


_GUIDANCE = {
    InstallOrigin.PACKAGE: (
        'This installation was identified as package-managed. Check the configured '
        'package source or its software manager for an Avelin update. A package may '
        'not have an update source configured; verify its origin before replacing it.'
    ),
    InstallOrigin.FLATPAK: (
        'This installation was identified as a Flatpak. Use the software manager '
        'or Flatpak tools for the installation and remote you trust. Check whether '
        'an Avelin update is actually available before applying changes.'
    ),
    InstallOrigin.SOURCE: (
        'This installation was identified as a source checkout. Consult the '
        'project\'s source instructions and review changes before updating your '
        'checkout. Preserve local modifications and back up important data.'
    ),
    InstallOrigin.UNKNOWN: (
        'Installation origin is unknown or conflicting. Identify how this copy '
        'was installed before choosing an update method. Do not assume a GitHub '
        'release or a version match means this installation is current or trusted.'
    ),
}


def update_guidance(verified_origins: Iterable[InstallOrigin] = ()) -> Guidance:
    """Select guidance from independently verified origins, conservatively.

    Only one distinct recognized origin produces specific guidance. Unknown,
    malformed or conflicting evidence fails closed. This function does not
    validate evidence, inspect the host, compare versions, or perform updates.
    """
    try:
        origins = set(verified_origins)
    except (TypeError, ValueError):
        origins = set()
    if len(origins) != 1:
        origin = InstallOrigin.UNKNOWN
    else:
        candidate = next(iter(origins))
        origin = candidate if isinstance(candidate, InstallOrigin) else InstallOrigin.UNKNOWN
    return Guidance(origin, _GUIDANCE[origin])
