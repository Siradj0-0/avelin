# Agent 12 — Docs, README and Housekeeping

Snapshot: main dbf19b5857b08943d42101e217043061c35c4824. Agent number 12 supplied 2026-11-06. agent-state exists; agents/agent12.md was absent when checked. 

## Current task
- PR #58 opened for #54 on agent12/readme-release-tags. Await independent review and CI; do not self-merge.
- GitHub MCP previously returned discovery failures; after 30 seconds a retry succeeded. Browser GitHub and gh are signed out; use MCP for writes.

## Backlog (investigate overlap and current main before each task)
1. Monitor PR #58 and follow up on review/CI for README tag-format correction.
2. Align source-setup unit-test instructions with the CI runner and self-tests; coordinate PR #18.
3. Document strict GTK accessibility test and skipped-test caveat; coordinate PR #18 and #20.
4. Validate PR #26 source guide power-profile wording on current main.
5. Link disposable packaging checks from contributor guidance; coordinate PR #18 and packaging owner.
6. Audit README dashboard claims after dashboard extraction PR lands.
7. Audit README storage and trash safety descriptions after cleanup changes land.
8. Audit source setup commands on an actual supported Debian/Ubuntu desktop or disposable environment.
9. Inspect gettext integration and scope a translation guide (do not claim support until implemented).
10. Review absence of PR template and propose concise verification/risk prompts.
11. Audit .editorconfig necessity and repository whitespace conventions before proposing one.
12. Review whether an accurate man page is feasible once installation/CLI stabilize; coordinate packaging.

## Verification
At main dbf19b5: `python3 -m unittest ci.test_run_unit_tests -v`: Ran 5 tests, OK. `python3 -m ci.run_unit_tests`: Ran 79 tests, OK (skipped=14). `python3 -m compileall -q avelin`: passed. GTK tests skipped; no UI or real-distro test.
