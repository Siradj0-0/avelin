# Agent 11 — Research and Product Ideas

## Current tasks
- PR #80, sourced PSI research for #50 and #37, awaits independent review. Branch `agent11/memory-pressure-research` at `9362b9932cf065cd253cd5990b209a0caf59a8f7`.
- PR #98, sourced boot-timing research for #93 and ideas #39/#42, awaits independent review. Branch `agent11/boot-timing-research` at `94c8af01c083bd0e29cdf46c1d355d087fee98a0`.
- PR #9: research/safety review posted with blocker about its proposed power-profile test and future integration; see https://github.com/Siradj0-0/avelin/pull/9#issuecomment-6695115514. Await revised head.
- Issues #84, #85, #101 and #107 filed: battery full/design context, future cleanup-preview freshness, scoped GLX renderer observations and cautious power-management overlap guidance. Agents 3 and 5 were asked to assess #84/#85 in #81 and #55; Agent 3 was asked to assess #101 against #7.
- Next research stream: compare existing Linux tuners and cleaners against the current product backlog; prioritize evidence-backed gaps and avoid duplicating #55 and #85. Graphics work may continue from #101.
- #38 overlaps PR #66's unmapped-view work; Agent 7 was asked to identify remaining sampling/measurement work after review. PR #66 is stacked on extraction and remains draft.

## Backlog, ranked approximately by impact over effort
1. #36 — read-only filesystem space and inode health (M).
2. #37 — memory-pressure context (M).
3. #38 — lower-overhead dashboard observation (M; partly covered by PR #66).
4. #41 — journal usage guidance without cleanup (S).
5. #85 — preview freshness and scope for future cleanup actions (M).
6. #39 — opt-in before/after boot snapshots (M).
7. #40 — read-only autostart inventory (M).
8. #84 — battery capacity context after #81 (M).
9. #42 — boot timing explainer (M).
10. #45 — read-only systemd health (M).
11. #101 — scoped renderer diagnostic, subject to hardware/desktop validation (M).
12. #43 — present existing compressed-swap collector after review (M).
13. #44 — bounded process-memory snapshot, privacy/performance gated (L).
14. #107 — cautious power-management overlap guidance (M).

## Decisions and constraints
- Identity assigned by user: Agent 11. Research owns `docs/research/` and `idea` issues; implementation is handed to owning agents.
- Agent 7 owns dashboard, including its existing `avelin/app.py` portions; extraction precedes Agent 6 shell extraction.
- No claims of guaranteed performance gains; distinguish observations, hypotheses, partial data, and unavailable data. Avoid destructive or privileged actions.
- Existing PR #13 is a compressed-swap collector; do not duplicate it. Power-profile changes are blocked due to #15. Coordinate storage with #31 and dashboard with #32.
- 2026-11-06 baseline at main `3a07f4d`: 82 tests passed, 14 skipped; compile check passed. PR #98 contains only 22 documentation lines and the tested document matches the remote blob. No visual UI test.
- Plain git push failed `fatal: could not read Username for 'https://github.com': terminal prompts disabled`; GitHub MCP successfully pushed identical files and commits with trailers. GitHub MCP intermittently returns HTTP 429/discovery failures; session spawn returned `The tool capability failed unexpectedly.` See #30 and #34.
