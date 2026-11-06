# Agent 9 — Updater, Privilege and Security

## Current task
- [#49](https://github.com/Siradj0-0/avelin/issues/49): document security boundaries and threat model; claimed by Agent 9.

## Backlog
1. Document existing and future privilege boundaries and threats (#49).
2. Review PR #3 power-profile writes against main's fail-closed guard.
3. Review PR #28 update redirect restriction and offline regression tests.
4. Define release metadata stable/prerelease comparison policy and test edge cases.
5. Design request coalescing, rate-limit cooldown and offline behavior for update checks.
6. Specify signed artifact trust, key rotation and rollback defenses before direct downloads.
7. Identify install methods and defer managed installations to native package managers.
8. Specify AppImage verified replacement and interruption safety before implementation.
9. Specify narrow polkit operations with direct-invocation validation and safe environments.
10. Build privilege-helper adversarial tests for auth boundaries when a helper exists.
11. Audit subprocess resolution and environment handling across security-sensitive code.
12. Review CI action pins and release-workflow permission/failure boundaries with Agent 8.
13. Plan package-format upgrade and failure-path tests with Agent 10.

## Decisions and observations
- Role number is 9; this state file was absent on 2026-11-06.
- No current privileged helper was identified in the inspected main tree; recheck before implementation.
- GitHub MCP is intermittent (HTTP 429 / discovery failures); browser is not signed in.
- Baseline on main: `PYTHONPATH=. python3 ci/run_unit_tests.py`: 79 tests, OK, 14 skipped; `python3 -m compileall -q avelin tests ci`: exit 0. Without `PYTHONPATH=.` tests failed with `ModuleNotFoundError: No module named 'avelin'`.
- Two subagent launches failed with `The tool capability failed unexpectedly.`
