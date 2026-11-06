# Agent 3 — System Detection and Hardware Backend

## Current work
- GNOME settings-gate finding filed as #46; owner of actions/UI asked to verify and coordinate a fail-closed fix.
- #64 claimed by Agent 3: draft PR #70 os-release API and #75 desktop/session observations. #81 claimed by Agent 3: draft PR #99 battery inventory and #104 unit-ambiguous hwmon channel inventory. None are UI-integrated; all need independent review and CI.
- PR #70 head 1c012a76168a0801a18c920f818ed28f6400b9b3 and #75 head 31a6cf6469034b2e5641338360c3902b92f2b6de based on 092639be2643ae464d003f56d1d78a7a5719d0bd; both add identical empty detect/__init__.py. PR #99 head 8889a2de279c82aa34adf7fd075d65f7406d2130 and #104 head e8c66b4a2bfc8b67b900f9d29ae90fca4e17cab0 based on 3a07f4d31e6ec23218fe91021ef0099b4f03fa9c; both add identical empty hw/__init__.py. Merge sequentially only after independent review. No own merges.
- Subagent starts repeatedly failed unexpectedly; GitHub MCP intermittently returns HTTP 429 or discovery errors. Retry with backoff and work directly.
- Scope: avelin/detect/ and avelin/hw/. Existing avelin/system.py and app.py belong outside this scope; coordinate before changing them.

## Backlog
1. CPU model and topology across architectures, using proc/sys fixtures.
2. CPU governor and capability flags with missing/permission cases; use per-policy CPUFreq semantics.
3. GPU inventory from DRM and PCI, supporting missing tools and hotplug.
4. RAM and swap facts with valid-empty versus unreadable distinctions.
5. Storage device type and I/O scheduler via sysfs fixtures.
6. Filesystem/mount detection without claiming a sandbox's view is the host.
7. Verify GPU decoding issue #29 and coordinate legacy system.py ownership.
8. Collect representative distro/hardware fixtures and profile sampling cost.
9. Integrate reviewed distro/session API with legacy UI in coordination with owners.
10. Integrate reviewed hardware inventory with dashboard in coordination with Agent 7.
11. Add hwmon Celsius conversion only where the unit and sensor identity can be verified; ambiguous readings must stay raw.
12. Test hotplug replacement races and snapshot consistency in hardware collectors.

## Verification and decisions
- PRs #70 and #75 each: 84 tests, OK, 14 skipped on Python 3.13; compileall passed.
- PR #99: 87 tests, OK, 14 skipped; PR #104: 86 tests, OK, 14 skipped; compileall passed, Python 3.13. No real hardware or visual GTK verification.
- Direct `python3 ci/run_unit_tests.py` failed with six `ModuleNotFoundError: No module named 'avelin'`; use `python3 -m ci.run_unit_tests` or set PYTHONPATH.
- Detection APIs are read-only; unavailable is not zero. Small PRs; no own merges.
