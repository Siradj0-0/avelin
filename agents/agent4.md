# Agent 4 — Optimization Catalog and Engine

Updated 2026-11-06. Scope: avelin/optimize/. No setting is applied by default. Privileged changes require Agent 9 coordination and a reviewed, narrowly scoped helper.

## Current work
- Create a data-only registry validator and tests after claiming a dedicated issue. Avoid duplicating PR #21 or integrating PR #3 blindly.
- PR #3: power writes must route through the existing fail-closed guard before merge. PR #8: high-risk split and review required; journal is outside this role.
- GitHub MCP discovery unavailable; browser signed in. Git CLI is not authenticated.

## Backlog
1. Define bounded registry schema with stable IDs, descriptions and source citations.
2. Validate risk tiers, reversibility and explicit irreversible warnings.
3. Validate typed read, apply, revert and preview descriptors; reject arbitrary shell commands.
4. Define distro, desktop and hardware applicability with unknown distinct from unsupported.
5. Test duplicate IDs, malformed files and version compatibility.
6. Add read-only capability checks and deterministic preview.
7. Model exact prior values and ownership-aware snapshots.
8. Design fail-closed verification and partial-failure states.
9. Specify conflict-aware rollback and uncertain outcomes.
10. Add cited memory sysctl candidates after schema and helper review.
11. Add cited CPU governor and I/O scheduler candidates with per-policy/device applicability.
12. Add read-only power-manager and DNS conflict diagnostics; no automatic changes.
13. Research journald retention and bootloader-specific recovery before proposing writes.
14. Coordinate privileged operations and polkit boundaries with Agent 9.
15. Review GPU per-application scope and hardware applicability; no global presets.

## Decisions and evidence
- Keep power-profile writes disabled: manual switches can cancel holds (issue #15).
- PR #8 audit suggested a temporary-file leak on early fchmod failure and wrong-thread exit hazard; ask its owner to verify through an issue before editing that file.
- Baseline on 2026-11-06: 79 tests passed, 14 skipped; compileall passed. No visual UI testing.
- Research candidates are not validated features or claims of performance benefit.
