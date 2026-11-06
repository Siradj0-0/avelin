# Agent 5 — Cleanup and Storage

## Current state
- Assigned area: `avelin/cleanup/`. Existing `avelin/storage.py` and `tests/` are outside the area; coordinate with their owners before editing.
- Identity resolved by user's 2026-11-06 instruction. `agent-state` exists; use the existing branch rather than replacing it. No existing `agents/agent5.md` was found on initial fetch.
- Coordination issue: https://github.com/Siradj0-0/avelin/issues/31. Related package-cache planner: https://github.com/Siradj0-0/avelin/pull/12. Avoid duplicating it.
- First proposed task: a small read-only preview result contract, isolated from the existing planner; claim in an issue before implementation.
- Baseline at `dbf19b5857b08943d42101e217043061c35c4824`: `python -m ci.run_unit_tests` ran 79 tests, OK (14 skipped); `python -m compileall -q avelin tests` passed. GTK was not visually tested.
- GitHub MCP intermittently responds with HTTP 429/discovery errors. Local `gh auth status` reports no GitHub login. Two subagent starts failed with `The tool capability failed unexpectedly.`

## Backlog
1. Define an immutable read-only preview result contract with unknown/partial size semantics.
2. Design trusted-root descriptor traversal with prefix-symlink rejection and fail-closed unsupported handling.
3. Handle mount boundaries, including same-device bind mounts; test in disposable namespace.
4. Estimate allocated bytes with hard-link deduplication, sparse files and partial statuses.
5. Coordinate APT/paccache previews with PR #12.
6. Inventory DNF5/zypper caches without promising an exact dry run.
7. Research old-kernel transaction previews with running and fallback kernel protection.
8. Preview journal/coredump use and distinguish active versus archived scope.
9. Inventory Flatpak refs without deleting app data or claiming shared bytes as savings.
10. Inventory Snap revisions and flag rollback loss; exclude snapshots.
11. Separate Docker/Podman caches from containers and volumes; indicate shared-layer uncertainty.
12. Discover configured pip/npm caches without destructive commands or whole tool-home deletion.
13. Research safe browser and Electron cache scoping; exclude profiles and user data.
14. Specify a separate confirmed deletion gate with explicit threat model and partial failure reporting.
15. Design bounded largest-folder reporting with exclusions and overlap handling.

## Safety decisions
Scans are read-only; observed bytes are not reclaimable-byte guarantees. No filesystem deletion, root escalation or broad prune in preview work. Handle unsupported tools and inaccessible paths without reporting zero. Every behavior change has tests; compile and run tests before pushing. Source-specific claims require primary citations. Do not merge own PR.
