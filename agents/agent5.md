# Agent 5 — Cleanup and Storage

## Current state
- Assigned area: `avelin/cleanup/`. Existing `avelin/storage.py`, `tests/`, and CI files are outside the area; coordinate with their owners before editing.
- User assigned Agent 5. The existing `agent-state` branch is authoritative; do not replace it. Coordination issue: https://github.com/Siradj0-0/avelin/issues/31.
- Preview contract task claimed in https://github.com/Siradj0-0/avelin/issues/55; first PR is https://github.com/Siradj0-0/avelin/pull/60, commit `5a35d4b98c4598e4c43afb2fa23e50c07491ea5d`. Await independent review; do not self-merge. Related package-cache planner https://github.com/Siradj0-0/avelin/pull/12 must not be duplicated.
- On base `092639be2643ae464d003f56d1d78a7a5719d0bd`, focused preview tests: 7 passed; `python -m ci.run_unit_tests`: 79 run, 14 skipped; `python -m compileall -q avelin tests`: passed. Pushed files matched tested files. GTK was not visually tested and Python 3.10 runtime was not tested.
- Preview tests currently require explicit invocation and are not in shared CI discovery; request Agent 10 coordination before modifying tests/CI.
- Independently reviewed PR #12 head `e7d7c518ba893041dd23f75235ff1dbead76879b`: https://github.com/Siradj0-0/avelin/pull/12#issuecomment-6694992796. Its branch suite passed 53 tests and compile check passed, but current CI runner is absent; rebase and exact-head re-review requested.
- Asked Agent 10 to coordinate discovery of cleanup tests: https://github.com/Siradj0-0/avelin/issues/55#issuecomment-6694981601.
- Filed storage boundary hardening issue https://github.com/Siradj0-0/avelin/issues/71; a disposable fixture confirmed a prefix symlink traverses outside its containing directory. Same-device bind mount not tested. Asked Agent 1 to identify owner before edits outside scope.
- Reviewed trash fix PR #25 at `54f5146eda574e778ac1513f57e7c7cd5cda45ed`: https://github.com/Siradj0-0/avelin/pull/25#issuecomment-6695082973. Suite ran 80 tests with 14 skipped; compile passed. Fake gio reproduced UnicodeDecodeError on merge base and warning on head; requested exact-head QA.
- GitHub MCP intermittently responds with HTTP 429/discovery errors. Local `gh auth status` reports no GitHub login. Four further subagent starts failed with `The tool capability failed unexpectedly.`

## Backlog
1. Integrate preview tests into shared CI, with Agent 10 coordination.
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

## Safety decisions and sources
Scans are read-only; observed bytes are not reclaimable-byte guarantees. No filesystem deletion, root escalation or broad prune in preview work. Handle unsupported tools and inaccessible paths without reporting zero. Every behavior change has tests; compile and run tests before pushing. Source-specific claims require primary citations. Do not merge own PR.

- Traversal/mount boundary: https://man7.org/linux/man-pages/man2/openat2.2.html
- Allocation and unlink caveats: https://man7.org/linux/man-pages/man2/statx.2.html and https://man7.org/linux/man-pages/man2/unlink.2.html
- Package caches: https://manpages.ubuntu.com/manpages/noble/man8/apt-get.8.html and https://man.archlinux.org/man/paccache.8
- Journals: https://man7.org/linux/man-pages/man1/journalctl.1.html
- Containers: https://docs.docker.com/reference/cli/docker/system/df/ and https://docs.podman.io/en/latest/markdown/podman-system-df.1.html
