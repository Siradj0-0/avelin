"""Pure, advisory cleanup plans. This module never executes or deletes anything.

Callers supply OS identity and independently observed package/tool evidence; no
filesystem, package-manager, network, environment or process access is performed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping
import re


class Presence(str, Enum):
    PRESENT = 'present'
    ABSENT = 'absent'
    UNKNOWN = 'unknown'


@dataclass(frozen=True)
class ToolEvidence:
    """Caller observations, not inferred from distro, PATH, or one another."""
    package: Presence = Presence.UNKNOWN
    executable: Presence = Presence.UNKNOWN

    def __post_init__(self) -> None:
        if not isinstance(self.package, Presence) or not isinstance(self.executable, Presence):
            raise ValueError('Evidence must use Presence values')


@dataclass(frozen=True)
class CleanupOption:
    id: str
    title: str
    package_name: str
    executable_name: str
    package_presence: Presence
    executable_presence: Presence
    scope: str
    proposed_effect: str
    reversibility: str
    risks: tuple[str, ...]
    preview_limitations: str
    source_urls: tuple[str, ...]
    # Never infer reclaimable space from cache size or from package availability.
    reclaimable_bytes: None = None
    approval_required: bool = True
    approval_obtained: bool = False

    @property
    def availability(self) -> Presence:
        """Both observations are required; contradictory evidence is unknown."""
        p, e = self.package_presence, self.executable_presence
        if p == e == Presence.PRESENT:
            return Presence.PRESENT
        if p == e == Presence.ABSENT:
            return Presence.ABSENT
        return Presence.UNKNOWN


@dataclass(frozen=True)
class CleanupPlan:
    distribution_id: str | None
    family: str | None
    matched_by: str | None
    options: tuple[CleanupOption, ...]
    notices: tuple[str, ...]


_APT = 'https://manpages.ubuntu.com/manpages/noble/man8/apt-get.8.html'
_DNF = 'https://dnf.readthedocs.io/en/latest/command_ref.html'
_PACCACHE = 'https://man.archlinux.org/man/paccache.8.en'
_ARCH = 'https://wiki.archlinux.org/title/Pacman'

# Explicit IDs take precedence over ordered ID_LIKE. No substring matching.
_FAMILIES = {
    'debian': 'debian', 'ubuntu': 'debian',
    'arch': 'arch', 'manjaro': 'arch',
    'fedora': 'dnf', 'rhel': 'dnf', 'centos': 'dnf',
    'rocky': 'dnf', 'almalinux': 'dnf',
}
_ID = re.compile(r'[a-z0-9._-]+\Z')


def _family(os_release: Mapping[str, str] | None) -> tuple[str | None, str | None, str | None]:
    """Use already-parsed os-release values; never source or execute the file."""
    if os_release is None:
        return None, None, None
    raw_id, raw_like = os_release.get('ID', ''), os_release.get('ID_LIKE', '')
    if not isinstance(raw_id, str) or not isinstance(raw_like, str):
        return None, None, None
    # A malformed ID or ID_LIKE cannot be used as distribution evidence.
    if raw_id and not _ID.fullmatch(raw_id):
        return None, None, None
    ident = raw_id or None
    if ident in _FAMILIES:
        return ident, _FAMILIES[ident], 'ID'
    likes = raw_like.split()
    if any(not _ID.fullmatch(item) for item in likes):
        return ident, None, None
    for item in likes:
        if item in _FAMILIES:
            return ident, _FAMILIES[item], 'ID_LIKE'
    return ident, None, None


def build_cleanup_plan(
    os_release: Mapping[str, str] | None = None,
    evidence: Mapping[str, ToolEvidence] | None = None,
) -> CleanupPlan:
    """Return static advice from supplied facts. Never requests or records approval.

    Evidence keys are the exact executable names apt-get, paccache and dnf.
    Missing evidence is unknown. Callers must independently establish evidence;
    it is a potentially stale observation, not an authorization to act.
    """
    distribution_id, family, matched_by = _family(os_release)
    observations = evidence if evidence is not None else {}
    if any(key not in ('apt-get', 'paccache', 'dnf') or not isinstance(value, ToolEvidence)
           for key, value in observations.items()):
        raise ValueError('Unexpected cleanup tool evidence')
    notices = (
        'Advisory only: no scans, commands, deletion, installation, or privilege changes are performed.',
        'Space potentially reclaimable is unknown; no candidates or sizes have been measured.',
        'Any future action requires separate explicit user approval; this plan does not obtain or grant it.',
        'Package and executable observations are supplied by the caller and may be stale or incomplete.',
    )
    if family is None:
        return CleanupPlan(distribution_id, None, None, (), notices + (
            'Distribution family is unsupported or unknown; no cleanup options are suggested.',))
    if matched_by == 'ID_LIKE':
        notices += ('Family inferred from ID_LIKE; compatibility is not guaranteed.',)

    specs = {
        'debian': ('apt-autoclean', 'APT obsolete archive cleanup', 'apt', 'apt-get',
            'System APT archive cache, subject to local APT configuration.',
            'Would remove cached package files that can no longer be downloaded; not installed packages.',
            ('Old cached packages may be needed for offline reinstalls or downgrades.',
             'APT configuration and repository state affect the candidates.'),
            'APT documents simulation, but this plan does not run it; non-root simulations may miss configuration and state can change.',
            (_APT,)),
        'arch': ('paccache', 'Pacman old archive cleanup', 'pacman-contrib', 'paccache',
            'Pacman configured package cache directories; configuration may change the locations.',
            'Would remove older cached package archives, retaining three versions per package by default; not installed packages.',
            ('The default also covers uninstalled packages; cached versions may be needed for offline reinstalls or downgrades.',
             'Local configuration and options affect the candidates.'),
            'Paccache documents a dry run, but this plan does not run it or enumerate candidates.',
            (_PACCACHE, _ARCH)),
        'dnf': ('dnf-packages', 'DNF cached package cleanup', 'dnf', 'dnf',
            'The executing user’s DNF cache; the root user has a separate system cache. Actual scope depends on configuration.',
            'Would remove cached package files, not installed packages; other repository metadata is not the intended target.',
            ('Caches may include data from disabled or removed repositories and other distribution versions.',
             'Cached packages may be needed for offline reinstalls or downgrades.',
             'DNF versions and configuration can differ; do not assume DNF5 has identical behavior.'),
            'No supported read-only candidate or size preview is claimed for DNF clean packages; this plan does not invoke DNF.',
            (_DNF,)),
    }
    option_id, title, package, executable, scope, effect, risks, limits, sources = specs[family]
    observed = observations.get(executable, ToolEvidence())
    option = CleanupOption(option_id, title, package, executable, observed.package, observed.executable,
                           scope, effect,
                           'Deletion is not automatically reversible; a package may need to be downloaded again and may no longer be available.',
                           risks, limits, sources)
    return CleanupPlan(distribution_id, family, matched_by, (option,), notices)
