# Cleanup plans: isolated advisory backend

`avelin.cleanup_plans` is a standalone, read-only **planning** API. It does not connect to the application UI, execute a preview or cleanup tool, scan files, invoke a shell, use sudo, change packages or delete anything. There is no execution API. It is not a promise that an option is safe on a particular machine. A future implementation would need a separate design and explicit per-action approval; this module neither requests nor records approval.

## Use and evidence

Pass already-parsed `os-release` fields and independently gathered observations. For example, the following is illustrative, not detection:

```python
from avelin.cleanup_plans import Presence, ToolEvidence, build_cleanup_plan

plan = build_cleanup_plan(
    {'ID': 'arch', 'ID_LIKE': ''},
    {'paccache': ToolEvidence(Presence.PRESENT, Presence.PRESENT)},
)
option = plan.options[0]
assert option.package_name == 'pacman-contrib'
assert option.reclaimable_bytes is None  # unknown, not zero
assert option.approval_required and not option.approval_obtained
```

Evidence is keyed by exact executable name: `apt-get`, `paccache`, or `dnf`. `package` describes whether the named distribution package is installed; `executable` describes whether the tool is available. Both are caller-supplied observations, not checks performed by this module; supply `UNKNOWN` for unverified, stale, inaccessible or ambiguous evidence. An executable on PATH does not prove package installation, and a distro does not prove either. `availability` is present only when both are present, absent only when both are absent, otherwise unknown (including conflicting evidence). This deliberately conservative summary does not replace the individual observations. It is not a guarantee the program works or can access a cache. Missing evidence defaults to unknown; malformed evidence is rejected.

Pass the result of a trusted, read-only os-release parser; never source the file as shell code. The module does not read it. Known `ID` takes precedence; otherwise the first recognized `ID_LIKE` is an explicitly labeled compatibility inference, not proof of tool compatibility. Unknown or malformed distributions yield no options. Derivatives and local configurations can differ. DNF5 compatibility is not asserted.

Each immutable option explains its package, tool, scope, effect, risks, reversibility and preview limitations. `reclaimable_bytes` is always `None`: nothing has been scanned or measured, and cache size alone is not reclaimable space. There is no total, candidate file list, or automatic recommendation. All options require separate explicit approval for any future action and show approval as not obtained; presence is never authorization. Removing caches is not automatically reversible; packages might no longer be downloadable, and a network re-download is not a backup.

## Research and boundaries

- **Debian/Ubuntu — APT:** [`apt-get` documentation](https://manpages.ubuntu.com/manpages/noble/man8/apt-get.8.html) describes autoclean as targeting cached archives no longer downloadable, unlike clean. Simulation is documented, but non-root configuration access and concurrent changes can distort it. No simulation is run here. APT configuration may change cache paths and candidates.
- **Arch — paccache:** [paccache manual](https://man.archlinux.org/man/paccache.8.en) documents the read-only dry run, configured cache directories and a default of three retained versions. The [Arch Wiki](https://wiki.archlinux.org/title/Pacman) explains that the default includes installed and uninstalled package archives and that the tool is in `pacman-contrib`. No dry run is executed here. Cached archives can support offline reinstalls or downgrades.
- **Fedora/RHEL family — DNF:** [DNF command reference](https://dnf.readthedocs.io/en/latest/command_ref.html) documents `clean packages`, user-specific caches versus root's system cache, and cleanup potentially including disabled repositories and other release versions. It does not establish a candidate or space preview for this operation; none is claimed or run. DNF5 is not assumed equivalent.
- **Distribution identification:** [systemd os-release specification](https://www.freedesktop.org/software/systemd/man/latest/os-release.html) specifies `ID` and ordered `ID_LIKE` fallback. Matching a family is not proof a package or tool is installed.

These are research references, not commands for the backend to run. Trash, personal files, journals, package removal, orphan removal, metadata cleanup and automated cleanup are deliberately out of scope. Scope and results can change with local configuration, permissions, concurrent package operations and distribution versions. Actual cleanup requires a separately reviewed implementation, clear confirmation, fresh checks and appropriate privileges; this module supplies none of these.

## Tests

Run `python3 -m unittest tests.test_cleanup_plans -v` and `python3 -m unittest discover -s tests -v`. Tests inject distro and tool observations, cover unknown and conflicting states and patch process/filesystem entry points to fail if called. They do not exercise real package managers or prove real-distro compatibility.
