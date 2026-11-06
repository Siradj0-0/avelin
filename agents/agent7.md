# Agent 7 — Dashboard and Visualization

## Current task
- Extract dashboard-only code from `avelin/app.py` into `avelin/dashboard/` without behavior changes. Claim: #32. Agent 6 extracts remaining shell after this PR merges.
- Main inspected at dbf19b5857b08943d42101e217043061c35c4824. Existing `agent-state` was found; `agents/agent7.md` did not exist.
- GitHub MCP is intermittently rate-limited; local `gh` is not authenticated. Subagent creation returned `The tool capability failed unexpectedly.`

## Backlog (unclaimed unless noted)
1. Extract dashboard into owned directory, preserve public Window behavior and tests.
2. Add deterministic graph tests for gaps, clipping, first samples and line patterns.
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
- Baseline `python -m ci.run_unit_tests`: 79 run, OK, 14 skipped; `python -m compileall -q avelin tests`: passed. GTK/visual testing unavailable locally: `gi` and `xvfb-run` absent.
