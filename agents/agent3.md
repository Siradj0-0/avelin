# Agent 3 — System Detection and Hardware Backend

## Current work
- GNOME settings-gate finding filed as #46; owner of actions/UI asked to verify and coordinate a fail-closed fix.
- Working from main dbf19b5857b08943d42101e217043061c35c4824; no prior agent3 state was present when checked.
- Two subagent starts failed unexpectedly; handle work directly and retry according to the requested backoff.
- Scope: avelin/detect/ and avelin/hw/. Existing avelin/system.py and app.py belong outside this scope; coordinate before changing them.

## Backlog
1. Implement fixture-testable os-release parsing with fallback and escaped values.
2. Implement desktop token and session type discovery as separate observations.
3. Implement optional read-only battery inventory with unavailable values.
4. Implement cautious thermal sensor discovery with honest labels.
5. CPU model and topology across architectures, using proc/sys fixtures.
6. CPU governor and capability flags with missing/permission cases.
7. GPU inventory from DRM and PCI, supporting missing tools and hotplug.
8. RAM and swap facts with valid-empty versus unreadable distinctions.
9. Storage device type and I/O scheduler via sysfs fixtures.
10. Filesystem/mount detection without claiming a sandbox's view is the host.
11. Review existing zram parser work in #23 and avoid duplication.
12. Verify GPU decoding issue #29 and coordinate legacy system.py ownership.
13. Collect representative distro/hardware fixtures and profile sampling cost.

## Verification and decisions
- Baseline main: `PYTHONPATH=. python3 ci/run_unit_tests.py`: 79 tests, OK, 14 skipped; `python3 -m compileall -q avelin tests`: passed, Python 3.13. This is not visual GTK verification.
- Direct `python3 ci/run_unit_tests.py` failed with six `ModuleNotFoundError: No module named 'avelin'`; use `python3 -m ci.run_unit_tests` or set PYTHONPATH.
- All detection APIs are read-only and should distinguish unavailable from zero. Prefer separate small PRs; no own merges.
