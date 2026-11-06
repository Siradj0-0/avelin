# Agent 9 — Updater, Privilege and Security

## Current work
- [PR #7 security review](https://github.com/Siradj0-0/avelin/pull/7#issuecomment-6695093222): no subprocess, privilege or deletion found in reviewed sampler; requested manageable split.
- [PR #25 safety review](https://github.com/Siradj0-0/avelin/pull/25#issuecomment-6695063064): no blocker in scoped error handling; high-risk review and QA still required.
- [PR #16 security review](https://github.com/Siradj0-0/avelin/pull/16#issuecomment-6695081733): no blocker in retired workflow scope; Agent 8 asked to confirm release gates.
- [PR #74](https://github.com/Siradj0-0/avelin/pull/74): threat model for [#49](https://github.com/Siradj0-0/avelin/issues/49); needs independent review. Do not self-merge.
- [PR #3 security review](https://github.com/Siradj0-0/avelin/pull/3#issuecomment-6695048371): changes requested; power writes bypass main's fail-closed guard. Mocked regression failed as expected.
- [PR #28 security review](https://github.com/Siradj0-0/avelin/pull/28#issuecomment-6695051418): no blocker in redirect-boundary scope at reviewed head; draft needs renewed review after changes.

## Backlog
1. Track independent review and updates for threat model PR #74.
2. Track PR #3 guard and regression changes; rereview exact new head.
3. Track PR #28 readiness and re-review if changed.
4. Define release metadata stable/prerelease comparison policy and test edge cases.
5. Design request coalescing, rate-limit cooldown and offline behavior for update checks.
6. Specify signed artifact trust, key rotation and rollback defenses before direct downloads.
7. Identify install methods and defer managed installations to native package managers.
8. Specify AppImage verified replacement and interruption safety before implementation.
9. Specify narrow polkit operations with direct-invocation validation and safe environments.
10. Build privilege-helper adversarial tests for authorization boundaries when a helper exists.
11. Audit subprocess resolution and environment handling across security-sensitive code.
12. Review CI action pins and release-workflow permission/failure boundaries with Agent 8.
13. Plan package-format upgrade and failure-path tests with Agent 10.

## Decisions and observations
- Role number is 9; no privileged helper was identified on inspected main.
- GitHub MCP intermittent: HTTP 429 / discovery failures; browser not signed in. Two subagent launches failed with `The tool capability failed unexpectedly.`
- PR #74 base `092639be2643ae464d003f56d1d78a7a5719d0bd`: `PYTHONPATH=. python3 ci/run_unit_tests.py`: 79 tests, OK, 14 skipped; `python3 -m compileall -q avelin tests ci`: exit 0.
- PR #3 head `3905c9308030a494cd6fe23bc1591ec86731ffa5`: 39 unittest tests pass; compileall passes; mocked no-power-set test fails. PR #28 head `9fbab5347a65999153d6f73d10f0f16b15a6f7bf`: 83 tests OK, 14 skipped; compileall passes.
- Running the main runner without `PYTHONPATH=.` failed with `ModuleNotFoundError: No module named 'avelin'`.
