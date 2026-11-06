# Agent 3 — System Detection and Hardware Backend

## Current work
- GNOME settings-gate finding filed as #46; owner of actions/UI asked to verify and coordinate a fail-closed fix.
- #64 is claimed by Agent 3. Draft PR #70 adds a stand-alone os-release API; not integrated into the UI or legacy system.py. Independent review and CI needed. The next task is separate desktop/session detection.
- PR #70 head 1c012a76168a0801a18c920f818ed28f6400b9b3, base 092639be2643ae464d003f56d1d78a7a5719d0bd. No own merges.
- Two subagent starts failed unexpectedly; handle work directly and retry according to the requested backoff.
- Scope: avelin/detect/ and avelin/hw/. Existing avelin/system.py and app.py belong outside this scope; coordinate before changing them.

## Backlog
1. Desktop token and session type discovery as separate observations.
2. Optional read-only battery inventory with unavailable values.
3. Cautious thermal sensor discovery with honest labels.
4. CPU model and topology across architectures, using proc/sys fixtures.
5. CPU governor and capability flags with missing/permission cases.
6. GPU inventory from DRM and PCI, supporting missing tools and hotplug.
7. RAM and swap facts with valid-empty versus unreadable distinctions.
8. Storage device type and I/O scheduler via sysfs fixtures.
9. Filesystem/mount detection without claiming a sandbox's view is the host.
10. Review existing zram parser work in #23 and avoid duplication.
11. Verify GPU decoding issue #29 and coordinate legacy system.py ownership.
12. Collect representative distro/hardware fixtures and profile sampling cost.

## Verification and decisions
- PR #70 local full suite on its base: `python3 -m ci.run_unit_tests`: 84 tests, OK, 14 skipped; `python3 -m compileall -q avelin tests`: passed, Python 3.13. Not visual GTK verification.
- Direct `python3 ci/run_unit_tests.py` failed with six `ModuleNotFoundError: No module named 'avelin'`; use `python3 -m ci.run_unit_tests` or set PYTHONPATH.
- All detection APIs are read-only and should distinguish unavailable from zero. Prefer separate small PRs.
