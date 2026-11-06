# Agent 12 — Docs, README and Housekeeping

Snapshot: main 092639be2643ae464d003f56d1d78a7a5719d0bd (PR #26 merged). Agent number 12 supplied 2026-11-06. agent-state exists; agents/agent12.md was absent when checked. 

## Current task
- PR #58 opened for #54 on agent12/readme-release-tags. Await independent review and CI; do not self-merge.
- PR #69 opened for #62 on agent12/source-ci-checks; await independent review and CI; do not self-merge.
- Reviewed PR #18 at 8f9dd774; requested rebase/current CI. Review: https://github.com/Siradj0-0/avelin/pull/18#issuecomment-6695022259
- GitHub MCP previously returned discovery failures; after 30 seconds a retry succeeded. Browser GitHub and gh are signed out; use MCP for writes.

## Backlog (investigate overlap and current main before each task)
1. Monitor PR #58 and follow up on review/CI for README tag-format correction.
2. Monitor PR #69 CI and independent review; coordinate contributor guide PR #18.
3. After PR #69, check strict GTK guide against changes from #20 and Agent 10.
4. Audit power safety wording after future backend or UI changes; PR #26 merged.
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

At PR #69 base 092639b, Python 3.13.15: runner self-tests 5 passed; project suite 79 passed, 14 skipped; compile and diff checks passed. Local /usr/bin/python3 is 3.9; GTK/Xvfb tests and documented system-Python commands not run.
