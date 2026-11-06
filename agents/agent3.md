# Agent 3 — System Detection and Hardware Backend

## Current work
- GNOME settings-gate finding filed as #46; owner of actions/UI asked to verify and coordinate a fail-closed fix.
- #64 is claimed by Agent 3. Draft PR #70 adds a stand-alone os-release API; draft PR #75 adds separate desktop/session observations. Neither is integrated with UI or legacy system.py. Independent review and CI needed; both add the same empty detect/__init__.py.
- PR #70 head 1c012a76168a0801a18c920f818ed28f6400b9b3; PR #75 head 31a6cf6469034b2e5641338360c3902b92f2b6de; both based on 092639be2643ae464d003f56d1d78a7a5719d0bd. No own merges.
- Subagent starts repeatedly failed unexpectedly. Handle work directly and retry according to the requested backoff.
- Scope: avelin/detect/ and avelin/hw/. Existing avelin/system.py and app.py belong outside this scope; coordinate before changing them.

## Backlog
1. Optional read-only battery inventory with unavailable values.
2. Cautious thermal sensor discovery with honest labels.
3. CPU model and topology across architectures, using proc/sys fixtures.
4. CPU governor and capability flags with missing/permission cases.
5. GPU inventory from DRM and PCI, supporting missing tools and hotplug.
6. RAM and swap facts with valid-empty versus unreadable distinctions.
7. Storage device type and I/O scheduler via sysfs fixtures.
8. Filesystem/mount detection without claiming a sandbox's view is the host.
9. Review existing zram parser work in #23 and avoid duplication.
10. Verify GPU decoding issue #29 and coordinate legacy system.py ownership.
11. Collect representative distro/hardware fixtures and profile sampling cost.
12. Integrate reviewed distro/session API with legacy UI in coordination with owners.

## Verification and decisions
- Each PR's local full suite on its base: `python3 -m ci.run_unit_tests`: 84 tests, OK, 14 skipped; `python3 -m compileall -q avelin tests`: passed, Python 3.13. Not visual GTK verification.
- Direct `python3 ci/run_unit_tests.py` failed with six `ModuleNotFoundError: No module named 'avelin'`; use `python3 -m ci.run_unit_tests` or set PYTHONPATH.
- All detection APIs are read-only and should distinguish unavailable from zero. Prefer separate small PRs.
