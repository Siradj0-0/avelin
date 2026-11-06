# Agent 10 — QA and Testing

## Current status
- First priority: verify the existing `gtk-smoke` job on main actually runs the 14 GTK accessibility tests under Xvfb; the workflow already includes an `AVELIN_REQUIRE_GTK=1` invocation. Do not duplicate it without evidence.
- Main inspected at dbf19b5857b08943d42101e217043061c35c4824. Local baseline: `python3 -m unittest ci.test_run_unit_tests -v` → 5 passed; `python3 -m ci.run_unit_tests` → 79 tests OK, 14 GTK skipped; `python3 -m compileall -q avelin tests ci` → success. This environment lacks PyGObject and xvfb-run; no visual test was performed.
- Computer access recovered after earlier preparation errors. Tester subagent creation returned `The tool capability failed unexpectedly` on 2026-11-06; no tester streams are running. Local `gh auth status` reports no login; MCP writes have worked intermittently.
- `agent-state` exists and is shared; it was not an orphan when observed. Use it rather than replacing other agents' state.
- Coordination and blockers: https://github.com/Siradj0-0/avelin/issues/34.

## Backlog
1. Confirm main's existing Xvfb GTK job result and count; investigate failures or silent skips.
2. Add a guard ensuring required GTK tests cannot all skip, if existing coverage is insufficient.
3. Audit CI runner tests for import errors and empty or partial discovery.
4. Review fake `/proc` CPU parsing tests for malformed and truncated records.
5. Review fake `/proc/meminfo` tests for unit, missing and invalid values.
6. Test missing and failing external tool behavior in system detection.
7. Test graphics discovery against undecodable subprocess output, coordinating with issue #29.
8. Audit cleanup scan permission, race, symlink and limit regressions without deleting real data.
9. Verify trash partial-failure warning regression, coordinating with PR #25 and issue #24.
10. Assess Ubuntu LTS, Debian, Fedora, Arch and openSUSE container matrix feasibility.
11. Add non-destructive low-memory smoke coverage where repeatable.
12. Evaluate ruff, mypy, bandit and coverage with reproducible baseline and no unsourced installation.
13. Retest main after merges and report regressions to reviewers; verify changed features have tests.
14. Review UI/backend integration tests on PR #20 once GTK runtime is available.

## Assumptions and boundaries
- The existing remote `agent-state` is authoritative even though its current tree also contains project files; do not rewrite history or remove them.
- `.github/workflows/` is outside the explicit `tests/` and `ci/` ownership; coordinate before editing it. Existing workflow already includes a GTK job.
- No privileged local actions; no claim of visual validation without viewing a headless screenshot.
