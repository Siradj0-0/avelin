# Agent 7 — Dashboard and Visualization

## Current tasks and blockers
- Draft PR #51 extracts dashboard code from `avelin/app.py` into `avelin/dashboard/`, no intended behavior change. Claim #32. Branch `agent7/dashboard-extraction`, commit `89db1410c015e618b838dc3e55512d3af55b2be3`.
- **Do not merge #51:** Debian packaging omits subpackages; requested Agent 8 coordination in #53. GTK integration and human visual test are outstanding. No local `gi` or `xvfb-run`. Requested Agent 10 include package-local tests in CI in #57.
- Draft PR #66 is stacked on #51: map/unmap sampling lifecycle, source cleanup, reset CPU baseline and insert graph gaps. Claim #38. Branch `agent7/pause-hidden-sampling`, commit `b4a5190260b5ca83a2d436a61f91c6757e9612f7`. Do not merge before #51; retarget/rebase once #51 lands. Mock tests do not prove GTK signal delivery; minimize/occlusion behavior and low-resource profiling remain unverified.
- Requested backend contracts from Agent 3 in #56. Agent 6 extracts the rest of the shell only after #51 merges.
- Reviewed #7 at `3fbc821a9de7420134c78149771d83ff548b0906`: independently reproduced known GPU replacement race; changes requested in #7 comment 6694947305, not approval.
- GitHub MCP intermittently returns 429/discovery errors; local `gh` is not authenticated. Two subagent creation calls returned `The tool capability failed unexpectedly.`

## Backlog
1. Complete #51 after packaging and GTK verification.
2. Ensure package-local dashboard regression tests run in CI (#57).
3. Verify and complete #66 lifecycle change after #51 merges (#38).
4. Agree capability-aware metrics contract with Agent 3 (#56).
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

## Verification
- Extraction: 3 dashboard tests OK; standard suite 79 run, OK, 14 skipped; compile passed. No visual validation claimed.
- Lifecycle: `python -m unittest avelin.dashboard.test_dashboard -q`: 4 tests OK; `python -m ci.run_unit_tests`: 79 run, OK, 14 skipped; `python -m compileall -q avelin tests`: passed; `git diff --check`: passed. Actual GTK lifecycle and visual tests outstanding.
- PR #7: 53 tests OK; compile and diff check passed; synthetic GPU replacement yielded `driver=amdgpu vendor=0x8086 busy=90 status=ok`. No real GPU test.

## Safety
No privileged operations or fabricated zeros. Preserve graph gaps; backend owns readers. Do not claim minimized or occluded windows always unmap.
