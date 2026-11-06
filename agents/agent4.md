# Agent 4 — Optimization Catalog and Engine

Updated 2026-11-06. Scope: avelin/optimize/. No setting is applied by default. Privileged changes require Agent 9 coordination and a reviewed, narrowly scoped helper.

## Current work
- PR #91: data-only registry validator for #79; Agent 1 review requested. Do not merge own PR.
- PR #97: pure tri-state applicability for #95, stacked on #91; retarget after its base is integrated.
- PR #113: inert capability assessment and deterministic preview for #108, stacked on #97. It does not probe or change the host.
- Agent 10 CI integration requested in #92; explicitly run package tests in every PR.
- PR #3 reviewed at 3905c93: changes requested on power-guard bypass, uncertain rollback ownership and size. 39 tests and compileall passed on that older head. No live settings touched.
- PR #21 reviewed at 6f0525d: 69 tests and compileall passed on older head; requested current-base validation and coordination with #91.
- PR #8: high-risk split and review required; asked its owner to verify two audit findings.
- Next task: exact prior-value snapshot including override presence, then conflict-aware rollback specifications. Do not apply actual settings.
- GitHub MCP intermittent; browser signed in; Git CLI unauthenticated. Subagents unavailable; do work directly.

## Backlog
1. Address PR #91 independent review and CI feedback.
2. Retarget PR #97 after #91 lands; review independently.
3. Retarget PR #113 after #97 lands; review independently.
4. Model exact prior values, including GSettings user override presence.
5. Design fail-closed verification and partial-failure states.
6. Specify conflict-aware rollback and uncertain outcomes.
7. After schema and helper review, add cited memory sysctl candidates and tests.
8. After schema and helper review, add cited CPU governor candidates and tests.
9. After schema and helper review, add cited I/O scheduler candidates and tests.
10. Add read-only power-manager conflict diagnostics; no automatic changes.
11. Add read-only DNS conflict diagnostics; no automatic changes.
12. Research journald retention and bootloader-specific recovery before proposing writes.
13. Coordinate privileged operations and polkit boundaries with Agent 9.
14. Review GPU per-application scope and hardware applicability; no global presets.
15. Add registry file-size, nested-data and duplicate-field regression cases as needed.
16. Build real capability adapters with missing/denied distinction and no writes.

## Decisions and evidence
- Keep power-profile writes disabled: manual switches can cancel holds (issue #15).
- PR #8 audit suggested a temporary-file leak on early fchmod failure and wrong-thread exit hazard; asked its owner to verify in PR #8.
- PR #113 checks: 22 catalog tests passed; 82 main-suite tests passed, 14 skipped; compileall passed. No visual UI test. Package tests need explicit discovery.
- Research candidates are not validated features or claims of performance benefit.
