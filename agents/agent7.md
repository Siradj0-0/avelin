# Agent 7 — Dashboard and Visualization

## Current task
- Draft PR #51 extracts the dashboard from `avelin/app.py` into `avelin/dashboard/` with no intended behavior change. Claim #32. Branch `agent7/dashboard-extraction`; commit `89db1410c015e618b838dc3e55512d3af55b2be3`.
- **Do not merge:** Debian package build copies only top-level Python files; package must include the new dashboard subpackage. Asked Agent 8 for coordination in #53. GTK visual and integration verification still needed; no local `gi` or `xvfb-run`.
- Headless tests in the new dashboard package run explicitly and are not currently included in CI discovery. Coordinate CI coverage with Agent 10.
- Agent 6 extracts the remaining shell after #51 merges.
- GitHub MCP intermittently returns 429/discovery errors; local `gh` is not authenticated. Two subagent creation calls returned `The tool capability failed unexpectedly.`

## Backlog (unclaimed unless noted)
1. Complete #51 extraction after packaging and GTK verification.
2. Ensure dashboard headless regression tests run in CI, coordinating with Agent 10.
3. Coordinate and implement hidden dashboard sampling pause and resume baseline (#38).
4. Agree capability-aware metrics contract with Agent 3 and explicitly preserve unavailable states.
5. Add bounded timestamped history and global device caps.
6. Persist history with retention and safe failure handling.
7. Add selectable ranges and bounded queries/downsampling.
8. Render per-core CPU using backend readers, with hotplug handling.
9. Show RAM, swap and zram clearly, coordinating #13 and #23.
10. Separate filesystem capacity from disk I/O using backend readers.
11. Add GPU/iGPU display only after hardware reader race review (#7).
12. Show per-interface network rates with reset handling.
13. Show labeled sensors and battery states through backend readers.
14. Add privacy-conscious bounded on-demand process view (#44).
15. Provide accessible graph history and validate assistive technology.
16. Add history export with explicit units and missing values.
17. Profile CPU, memory and wakeups on constrained hardware.

## Decisions and validation
- Do not duplicate backend readers. Agent 3 owns backend; Agent 6 owns non-dashboard shell.
- No privileged operations or fabricated zeros. Preserve graph gaps.
- `python -m unittest avelin.dashboard.test_dashboard -q`: 3 tests, OK. `python -m ci.run_unit_tests`: 79 run, OK, 14 skipped. `python -m compileall -q avelin tests`: passed. AST comparison confirmed moved draw/sample unchanged; layout differs only by its local helper import. No visual validation claimed.
