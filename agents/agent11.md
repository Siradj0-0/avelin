# Agent 11 — Research and Product Ideas

## Current tasks
- PR #80, research note for #50 and #37, awaits independent review. Branch `agent11/memory-pressure-research` at `9362b9932cf065cd253cd5990b209a0caf59a8f7`. No application changes.
- Next: post research/safety review of PR #9: its proposed power-profile test and future integration do not address loss of holds documented in #15. A prior attempt returned MCP discovery failure; retry.
- Continue product-idea research; coordinate with Agent 7 on dashboard and Agent 5 on cleanup.

## Backlog, ranked approximately by impact over effort
1. #36 — read-only filesystem space and inode health (M).
2. #37 — memory-pressure context (M).
3. #38 — lower-overhead dashboard observation (M).
4. #41 — journal usage guidance without cleanup (S).
5. #39 — opt-in before/after boot snapshots (M).
6. #40 — read-only autostart inventory (M).
7. #42 — boot timing explainer (M).
8. #45 — read-only systemd health (M).
9. #43 — present existing compressed-swap collector after review (M).
10. #44 — bounded process-memory snapshot, privacy/performance gated (L).

## Decisions and constraints
- Identity assigned by user: Agent 11. Research owns `docs/research/` and `idea` issues; implementation is handed to owning agents.
- Agent 7 owns dashboard, including its existing `avelin/app.py` portions; extraction precedes Agent 6 shell extraction.
- No claims of guaranteed performance gains; distinguish observations, hypotheses, partial data, and unavailable data. Avoid destructive or privileged actions.
- Existing PR #13 is a compressed-swap collector; do not duplicate it. Power-profile changes are blocked due to #15. Coordinate storage with #31 and dashboard with #32.
- 2026-11-06 baseline at main `092639b`: 79 tests passed, 14 skipped; compile check passed. PR #80 contains only 24 documentation lines and the tested document matches the remote blob. No visual UI test.
- Plain git push failed `fatal: could not read Username for 'https://github.com': terminal prompts disabled`; GitHub MCP successfully pushed the identical file and commit with trailer. GitHub MCP intermittently returns HTTP 429/discovery failures; session spawn returned `The tool capability failed unexpectedly.` See #30 and #34.
