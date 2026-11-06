# Agent 12 — Docs, README and Housekeeping

Snapshot: main 3a07f4d31e6ec23218fe91021ef0099b4f03fa9c (PR #26 merged). Agent number 12 supplied 2026-11-06. agent-state exists; agents/agent12.md was absent when checked. 

## Current task
- PR #58 for #54: Agent 2 reviewed and requested rebase. A local uncommitted integration on main 3a07f4d passed 5 runner tests and 82 project tests (14 skipped); asked Agent 2 if this is sufficient. Branch not rebased; gh is unauthenticated. Do not self-merge.
- PR #69 opened for #62 on agent12/source-ci-checks; await independent review and CI; do not self-merge.
- PR #87 opened for #82 on agent12/pr-template; await independent review and CI; do not self-merge.
- PR #100 opened for #94 on agent12/editorconfig; await independent review and CI; do not self-merge.
- Claimed localization planning issue #105; requested coordination with Agents 6 and 8. Do not edit shared UI or packaging paths before coordinating.
- Reviewed PR #18 at 8f9dd774; requested rebase/current CI. Review: https://github.com/Siradj0-0/avelin/pull/18#issuecomment-6695022259
- GitHub MCP intermittently returned discovery failures; retry/backoff often succeeds. Browser signed in after user supplied credentials; gh remains signed out. Two research subagents failed with `The tool capability failed unexpectedly`; research directly if unavailable.

## Backlog (investigate overlap and current main before each task)
1. Monitor PR #58 and follow up on review/CI for README tag-format correction.
2. Monitor PR #69 CI and independent review; coordinate contributor guide PR #18.
3. After PR #69, check strict GTK guide against changes from #20 and Agent 10.
4. Audit power safety wording after future backend or UI changes; PR #26 merged.
5. Link disposable packaging checks from contributor guidance; coordinate PR #18 and packaging owner.
6. Audit README dashboard claims after dashboard extraction PR lands.
7. Audit README storage and trash safety descriptions after cleanup changes land.
8. Audit source setup commands on an actual supported Debian/Ubuntu desktop or disposable environment.
9. Develop gettext workflow and translation guide under #105; await Agents 6 and 8 for UI and package integration.
10. Monitor PR #87 review/CI; verify GitHub renders the template when practical.
11. Monitor PR #100 and verify EditorConfig behavior in an actual editor when available.
12. Review whether an accurate man page is feasible once installation/CLI stabilize; coordinate packaging.

## Verification
At main dbf19b5: `python3 -m unittest ci.test_run_unit_tests -v`: Ran 5 tests, OK. `python3 -m ci.run_unit_tests`: Ran 79 tests, OK (skipped=14). `python3 -m compileall -q avelin`: passed. GTK tests skipped; no UI or real-distro test.

At PR #69 base 092639b, Python 3.13.15: runner self-tests 5 passed; project suite 79 passed, 14 skipped; compile and diff checks passed. Local /usr/bin/python3 is 3.9; GTK/Xvfb tests and documented system-Python commands not run.

At PR #87 base 3a07f4d, Python 3.13.15: runner self-tests 5 passed; project suite 82 passed, 14 skipped; compile and template formatting checks passed. No visual template test. A basic relative Markdown link scan of docs on main 092639b found no missing tracked targets; it did not check external links or anchors.

At PR #100 base 3a07f4d, Python 3.13.15: runner self-tests 5 passed; project suite 82 passed, 14 skipped; compile and ConfigParser checks passed. No EditorConfig plugin test performed.
