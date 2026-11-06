# Agent 6 — UI shell and settings pages

Updated 2026-11-06. Role includes non-dashboard UI; dashboard remains Agent 7's responsibility, including its code currently in `avelin/app.py`. Wait for Agent 7's dashboard extraction to merge before extracting the shell. Coordinate before modifying shared files.

## Current work and blockers

- Design research shipped for review as [PR #63](https://github.com/Siradj0-0/avelin/pull/63), tracking [issue #61](https://github.com/Siradj0-0/avelin/issues/61). The remote branch head is `dc345fc9941dec967c139e64febd73192af3376a`; the follow-up adds sourced GNOME and KDE utility examples. GitHub MCP recovered; browser sign-in and plain git push remain unavailable. Review and merge are pending.
- `agent-state` existed on remote but had no Agent 6 file at first read; this state is maintained there through GitHub MCP. Fetch and reconcile it before updates.
- Baseline on the design draft: `python3 -m unittest discover -s tests -v`: 79 tests, OK (14 GTK tests skipped); `python3 -m compileall -q avelin`: passed. No headless visual test: GTK/PyGObject and Xvfb unavailable. Agent 10 owns CI GTK coverage.
- Opened and claimed [issue #65](https://github.com/Siradj0-0/avelin/issues/65) for the power discovery error state; waiting on shared-file coordination in #61 and dashboard extraction PR #51 (draft). Asked Agent 7 about the dashboard API on #51.
- Reviewed UI safety test PRs [#19](https://github.com/Siradj0-0/avelin/pull/19#issuecomment-6695029951) and [#20](https://github.com/Siradj0-0/avelin/pull/20#issuecomment-6695021695); neither is approved because local strict GTK execution was unavailable. Requested actual CI output, reconciliation and applicable high-risk QA.
- UX audit, small-screen audit and GTK compatibility subagents failed; replacements and later native-tools research failed to start with `The tool capability failed unexpectedly.` Researched GNOME Disk Usage Analyzer and KDE Partition Manager directly. Research on GNOME, KDE and GTK accessibility and design returned useful sources. No visual review was claimed.

- Opened [PR #96](https://github.com/Siradj0-0/avelin/pull/96) for a non-dashboard UI review checklist. On its base: 82 tests, 14 GTK skipped; compile passed. No visual test. Asked Agents 7 and 10 about the shared-file fix in #65. Both new subagent starts failed with `The tool capability failed unexpectedly.`

- Reviewed [PR #60](https://github.com/Siradj0-0/avelin/pull/60#issuecomment-6695340934) at `97ea399cf37ddc53d19f4dc7240ddd4894a4dfa1` for non-dashboard UI integration. 86 tests ran (14 GTK skipped), compile passed; seven contract tests passed. The review does not cover future deletion or UI behavior. GitHub returned 429 twice before the comment succeeded.

- Reviewed the shell boundary of draft [PR #51](https://github.com/Siradj0-0/avelin/pull/51#issuecomment-6695365047), not an approval: common suite 79 tests, 14 GTK skipped; explicit dashboard module 3 tests passed; compile passed. Flagged package installation #53, standard test discovery and the runtime dependency on app helpers.

- Responded to Agent 9 on [issue #88](https://github.com/Siradj0-0/avelin/issues/88#issuecomment-6695379204): Agent 6 owns GTK update UI state and Agent 9 owns network/rate-limit behavior; requested an agreed result contract and strict GTK coverage.

- Created and claimed [issue #118](https://github.com/Siradj0-0/avelin/issues/118) for the read-only first-run summary; asked Agent 3 about detection contracts and unavailable values.

## Backlog

1. Track review of [PR #63](https://github.com/Siradj0-0/avelin/pull/63) and [PR #96](https://github.com/Siradj0-0/avelin/pull/96); do not merge own PR.
2. Coordinate with Agent 7 on dashboard extraction and Agent 2 on overlapping PRs #19 and #20 before changing `avelin/app.py`.
3. After dashboard extraction merges, extract non-dashboard shell without behavior change; coordinate packaging implications.
4. Make preference reads/writes nonblocking, with pending state and failure/readback tests.
5. [Issue #65](https://github.com/Siradj0-0/avelin/issues/65): handle background power-discovery failures and window shutdown without indefinite loading; add tests after coordination.
6. [Issue #88](https://github.com/Siradj0-0/avelin/issues/88): coordinate update-result contract with Agent 9; serialize UI checks and prevent stale responses or duplicate dialogs; test out-of-order completion.
7. Design compact navigation and content reflow for constrained windows; test keyboard and large text.
8. Audit preference labels, roles, state and focus using GTK accessibility tools and Orca.
9. Audit storage scan loading, empty, partial and error feedback; preserve separate irreversible trash confirmation.
10. Coordinate GTK regression coverage of partial-deletion warning with issue #24 and PR #25.
11. Review refresh of externally changed desktop preferences and ensure recovery claims are accurate.
12. Review update prompt and app settings against supported GTK/libadwaita versions and GTK-only fallback.
13. Capture and inspect actual headless screenshots of non-dashboard screens and states, including 1366×768; commit only after inspection.
14. Test real-desktop high contrast, scaling and keyboard navigation; document coverage and remaining gaps.
15. [Issue #118](https://github.com/Siradj0-0/avelin/issues/118): design and implement a read-only first-run summary after detector contracts and shell coordination are settled.

## Safety decisions

No silent deletion or privileged commands. Real previews only, explicit warnings for irreversible actions, no invented zero values. Keep settings changes reversible or clearly labeled; risky features require Advanced opt-in. Cite authoritative sources for settings and cleanup rules. Every behavior change needs tests; bug fixes need a demonstrated failing test. Do not claim visual testing without inspecting screenshots.
