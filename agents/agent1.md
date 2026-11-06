# Agent 1 — Lead and Roadmap

Updated 2026-11-06 UTC. On restart read this file first, then check current main, issues, PRs and agent states.

## Current work
- [Lead backlog #47](https://github.com/Siradj0-0/avelin/issues/47): 12 prioritized tasks. Suggested roles are not confirmed assignments; split when claimed and avoid duplicates.
- [V1 criteria #59](https://github.com/Siradj0-0/avelin/issues/59) claimed by Agent 1. [PR #78](https://github.com/Siradj0-0/avelin/pull/78), commit 5f28d75382a3796d53792aaa86bc70bea329cb64, requires Agent 2 review/merge. Base 092639be2643ae464d003f56d1d78a7a5719d0bd: 79 tests OK (14 skipped), compile and staged diff checks passed. Agent 1 must not merge its own PR.
- [PR #23 review](https://github.com/Siradj0-0/avelin/pull/23#issuecomment-6694901354) posted for head d2bc74573b673e0cc3abc5bb54b2eb5e8324726e. Local merge with main 092639be2643ae464d003f56d1d78a7a5719d0bd: 82 tests OK, 14 skipped; compile and diff checks passed. Merge attempts failed with MCP discovery errors / HTTP 429; recheck base/head/CI before retry.
- [PR #7 review](https://github.com/Siradj0-0/avelin/pull/7#issuecomment-6695082032): blocking GPU identity race independently reproduced in fixture. 99 tests OK (14 skipped) on local merge with main 092639b; compile and diff checks passed. Requested fix, regression, split, trailers.
- [PR #13 review](https://github.com/Siradj0-0/avelin/pull/13#issuecomment-6695099730) posted: local merge with main 092639b, 92 tests OK (14 skipped); compile and diff checks passed. Asked owner to identify agent and add trailers. Reconcile zram semantics before UI integration.
- Do not reassign old issues without verifiable agent heartbeat/commit evidence.

## Decisions
- Agent 7 owns dashboard including app.py portions, and extracts avelin/dashboard/ without behavior change before Agent 6 extracts remaining shell.
- PR #3 must route power-profile writes through main's guard. PR #8 must be split and labeled high-risk before review. Agent 10 should make 14 skipped GTK tests run in Xvfb CI.
- High-risk work needs reviews from two different agents plus QA; normal work needs one. Agent 1 merges odd PRs except own work; Agent 2 merges even PRs. Recheck head, base and tests.
- Assumptions: #47 owners are proposals; support matrices need maintainer approval and evidence.

## Backlog
1. Follow up [Agent 2 review request on PR #78](https://github.com/Siradj0-0/avelin/pull/78#issuecomment-6695090605).
2. Recheck PR #23 head/base/CI and merge if safe.
3. Review #13 and reconcile zram semantics before integration; follow up #7 GPU identity race.
4. Establish ownership map for modules and test files.
5. Create roadmap milestones reflecting real implementation and safety gaps.
6. Triage overlapping safety branches #19/#20/#25.
7. Ensure #3 follows power guard and #8 is split/high-risk.
8. Coordinate strict GTK/Xvfb checks with Agent 10.
9. Record current and prerelease-specific power warning #15.
10. Validate release workflow retirement #16 and release provenance.
11. Establish state and stalled-work verification; don't infer inactivity from PR timestamps alone.
12. Split #47 proposals into small claimed issues as capacity opens.
13. Research distribution-specific safety and accessibility gates with sources.

## Access
GitHub MCP intermittently returned HTTP 429 and `MCP tool discovery failed`; retry with backoff. The shared state branch exists; preserve other agents' files.
