# Agent 3 — System Detection and Hardware Backend

## Current work
- GNOME settings-gate finding filed as #46; owner of actions/UI asked to verify and coordinate a fail-closed fix.
- #64 claimed: draft PR #70 os-release and #75 desktop/session observations. #81 claimed: #99 battery and #104 hwmon raw channel inventories. #111 claimed: #115 CPUFreq policy observations. All are Agent 3 draft PRs, backend-only, not UI-integrated, and require independent review and CI.
- PR #70 head 1c012a76168a0801a18c920f818ed28f6400b9b3 and #75 head 31a6cf6469034b2e5641338360c3902b92f2b6de based on 092639be2643ae464d003f56d1d78a7a5719d0bd; both add identical empty detect/__init__.py. #99 head 8889a2de279c82aa34adf7fd075d65f7406d2130 and #104 head e8c66b4a2bfc8b67b900f9d29ae90fca4e17cab0 based on 3a07f4d31e6ec23218fe91021ef0099b4f03fa9c. #115 head 2fe2bb1c0999597c8f8d69fa01bb2e2d88a71ceb based on 70b5eb40494cef6c2e1534ab0ff84844e8081901. The latter three all add identical empty hw/__init__.py; merge sequentially with fresh CI. No own merges.
- Subagent starts repeatedly failed unexpectedly; GitHub MCP intermittently returns HTTP 429 or discovery errors. Retry with backoff and work directly.
- Scope: avelin/detect/ and avelin/hw/. Existing avelin/system.py and app.py belong outside this scope; coordinate before changing them.

## Backlog
1. CPU model and topology across architectures, using proc/sys fixtures.
2. CPU capability flags with missing and permission cases.
3. GPU inventory from DRM and PCI, supporting missing tools and hotplug.
4. RAM and swap facts with valid-empty versus unreadable distinctions.
5. Storage device type and I/O scheduler via sysfs fixtures.
6. Filesystem/mount detection without claiming a sandbox's view is the host.
7. Verify GPU decoding issue #29 and coordinate legacy system.py ownership.
8. Collect representative distro/hardware fixtures and profile sampling cost.
9. Integrate reviewed distro/session API with legacy UI in coordination with owners.
10. Integrate reviewed hardware inventory with dashboard in coordination with Agent 7.
11. Add hwmon Celsius conversion only where unit and sensor identity can be verified; ambiguous readings must stay raw.
12. Test hotplug replacement races and snapshot consistency in hardware collectors.

## Verification and decisions
- PRs #70 and #75 each: 84 tests, OK, 14 skipped; #99: 87 tests, 14 skipped; #104: 86 tests, 14 skipped; #115: 85 tests, 14 skipped. Each had compileall pass on Python 3.13. No real hardware or visual GTK verification.
- Direct `python3 ci/run_unit_tests.py` failed with six `ModuleNotFoundError: No module named 'avelin'`; use `python3 -m ci.run_unit_tests` or set PYTHONPATH.
- Detection APIs are read-only; unavailable is not zero. Small PRs; no own merges.
