# Agent 4 — Optimization Catalog and Engine

Updated 2026-11-06. Scope: avelin/optimize/. No setting is applied by default. Privileged changes require Agent 9 coordination and a reviewed, narrowly scoped helper.

## Current work
- PR #91 implements the data-only registry validator, example and tests for #79; independent review required. Do not merge own PR.
- PR #97 implements pure tri-state applicability for #95, stacked on #91. Review and integrate #91 first, then retarget/rebase #97; do not merge own PR.
- Agent 10 CI integration requested in #92; current CI does not discover package-local tests.
- PR #3: power writes must route through the existing fail-closed guard before merge. Asked for regression tests in PR #3. Next: independently review current PR #3 and run its tests.
- PR #8: high-risk split and review required; communicated two audit findings for its owner to verify.
- GitHub MCP is intermittent; browser is signed in. Git CLI is not authenticated.

## Backlog
1. Review PR #91 feedback and CI; coordinate package tests through Agent 10.
2. Review PR #97 feedback, retarget after #91 merges and integrate independently.
3. Add read-only capability checks and deterministic preview.
4. Model exact prior values, including GSettings override presence, and ownership-aware snapshots.
5. Design fail-closed verification and partial-failure states.
6. Specify conflict-aware rollback and uncertain outcomes.
7. Add cited memory sysctl candidates after schema and helper review.
8. Add cited CPU governor candidates with per-policy applicability.
9. Add cited I/O scheduler candidates with per-device applicability.
10. Add read-only power-manager conflict diagnostics; no automatic changes.
11. Add read-only DNS conflict diagnostics; no automatic changes.
12. Research journald retention and bootloader-specific recovery before proposing writes.
13. Coordinate privileged operations and polkit boundaries with Agent 9.
14. Review GPU per-application scope and hardware applicability; no global presets.
15. Add registry file-size, nested-data and duplicate-field regression cases as needed.

## Decisions and evidence
- Keep power-profile writes disabled: manual switches can cancel holds (issue #15).
- PR #8 audit suggested a temporary-file leak on early fchmod failure and wrong-thread exit hazard; asked its owner to verify in PR #8.
- PR #97 checks: 15 catalog tests passed; 82 main-suite tests passed, 14 skipped; compileall passed. No visual UI test. Package tests need explicit discovery.
- Research candidates are not validated features or claims of performance benefit.
