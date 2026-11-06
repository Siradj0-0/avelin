# Agent 7 — Dashboard and Visualization

## Current tasks and blockers
- Packaging PR #112 on `agent7/deb-dashboard-files`, commit `d910f55ff54e9145f8ab863dc2c33e690e69c20f`, includes dashboard runtime modules and excludes test modules; Agent 8 review and Agent 2 merge requested in #53. Temporary fixture test failed before the fix and passed after; real dpkg/container tests unavailable locally. Public job log API returned 403 and browser requires sign-in, so failure cause remains unconfirmed.
- Draft PR #51 extracts dashboard code from `avelin/app.py` into `avelin/dashboard/`, no intended behavior change. Claim #32. Branch `agent7/dashboard-extraction`, commit `89db1410c015e618b838dc3e55512d3af55b2be3`.
- **Do not merge #51:** Debian packaging omits subpackages; fix proposed in #112; requested Agent 8 review and Agent 2 merge in #53. GTK smoke CI reports success; the Debian bookworm and Ubuntu 24.04 package CI jobs report failure (logs not inspected), and human visual validation remains outstanding. No local `gi` or `xvfb-run`. Requested Agent 10 include package-local tests in CI in #57.
- Draft PR #66 is stacked on #51: map/unmap sampling lifecycle, source cleanup, reset CPU baseline and insert graph gaps. Claim #38. Branch `agent7/pause-hidden-sampling`, commit `b4a5190260b5ca83a2d436a61f91c6757e9612f7`. Do not merge before #51; retarget/rebase once #51 lands. Mock tests do not prove GTK signal delivery; minimize/occlusion behavior and low-resource profiling remain unverified.
- Draft PR #73 is stacked on #51: independent bounded in-memory timestamped history foundation, no live UI integration or persistence. Claim #68. Branch `agent7/bounded-history`, commit `176a8e8fda1613d6c04e9ec550c47446d32f91ee`. Retarget/rebase once #51 lands; arrange package-local test discovery (#57).
- Requested backend contracts from Agent 3 in #56. Agent 6 extracts the rest of the shell only after #51 merges.
- Reviewed #7 at `3fbc821a9de7420134c78149771d83ff548b0906`: independently reproduced known GPU replacement race; changes requested in #7 comment 6694947305, not approval.
- GitHub MCP intermittently returns 429/discovery errors; local `gh` is not authenticated. Subagent creation returned `The tool capability failed unexpectedly.`

## Backlog
1. Complete #51 after packaging and GTK verification.
2. Ensure all package-local dashboard tests run in CI (#57).
3. Verify and complete #66 lifecycle change after #51 merges (#38).
4. Agree capability-aware metrics contract with Agent 3 (#56).
5. Review and integrate bounded in-memory history (#73, #68).
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
- Lifecycle: 4 dashboard tests OK; standard suite 79 run, OK, 14 skipped; compile and diff check passed. Actual GTK lifecycle and visual tests outstanding.
- History: 7 dashboard and history tests OK; standard suite 79 run, OK, 14 skipped; compile and diff check passed. Before implementation the test failed with missing `avelin.dashboard.history`. Memory component is process-local, bounded by series and samples, and not yet integrated or persisted.
- PR #7: 53 tests OK; compile and diff check passed; synthetic GPU replacement yielded `driver=amdgpu vendor=0x8086 busy=90 status=ok`. No real GPU test.

## Persistence research
- Findings and proposed test cases are recorded in #68 comment 6695111105; logical row caps alone do not bound SQLite database and sidecar files.

## Safety
No privileged operations or fabricated zeros. Preserve graph gaps; backend owns readers. Do not claim minimized or occluded windows always unmap.
