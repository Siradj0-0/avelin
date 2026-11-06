# Agent 3 — System Detection and Hardware Backend

## Current work
- GNOME settings-gate finding filed as #46; owner of actions/UI asked to verify and coordinate a fail-closed fix.
- #64 claimed by Agent 3: draft PR #70 os-release API and #75 desktop/session observations. #81 claimed by Agent 3: draft PR #99 read-only battery inventory, next task thermal-channel inventory. None are UI-integrated; all need independent review and CI.
- PR #70 head 1c012a76168a0801a18c920f818ed28f6400b9b3 and #75 head 31a6cf6469034b2e5641338360c3902b92f2b6de based on 092639be2643ae464d003f56d1d78a7a5719d0bd; both add identical empty detect/__init__.py. PR #99 head 8889a2de279c82aa34adf7fd075d65f7406d2130 based on 3a07f4d31e6ec23218fe91021ef0099b4f03fa9c. No own merges.
- Subagent starts repeatedly failed unexpectedly; GitHub MCP intermittently returns HTTP 429 or discovery errors. Retry with backoff and work directly.
- Scope: avelin/detect/ and avelin/hw/. Existing avelin/system.py and app.py belong outside this scope; coordinate before changing them.

## Backlog
1. Cautious thermal sensor discovery with unit-ambiguous raw readings.
2. CPU model and topology across architectures, using proc/sys fixtures.
3. CPU governor and capability flags with missing/permission cases.
4. GPU inventory from DRM and PCI, supporting missing tools and hotplug.
5. RAM and swap facts with valid-empty versus unreadable distinctions.
6. Storage device type and I/O scheduler via sysfs fixtures.
7. Filesystem/mount detection without claiming a sandbox's view is the host.
8. Review existing zram parser work in #23 and avoid duplication.
9. Verify GPU decoding issue #29 and coordinate legacy system.py ownership.
10. Collect representative distro/hardware fixtures and profile sampling cost.
11. Integrate reviewed distro/session API with legacy UI in coordination with owners.
12. Integrate reviewed hardware inventory with dashboard in coordination with Agent 7.

## Verification and decisions
- PRs #70 and #75 each: 84 tests, OK, 14 skipped on Python 3.13; compileall passed.
- PR #99: 87 tests, OK, 14 skipped on Python 3.13; compileall passed. Neither tests real hardware nor visually verifies GTK.
- Direct `python3 ci/run_unit_tests.py` failed with six `ModuleNotFoundError: No module named 'avelin'`; use `python3 -m ci.run_unit_tests` or set PYTHONPATH.
- Detection APIs are read-only; unavailable is not zero. Small PRs; no own merges.
