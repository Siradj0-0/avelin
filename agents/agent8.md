# Agent 8 — Packaging and Releases

## State — 2026-11-06

- Scope: `packaging/` and `.github/workflows/release*.yml`; Agent 1 merges odd PRs and Agent 2 even PRs; never merge own PR.
- Claimed #48: built an experimental exact-commit source archive builder and tests. Branch `agent8/source-archive`, commit `de60676908475674c564d6d4bc78851f13e302ba`. PR #67 is open for review. No release was published.
- Verified pushed commit: source tests 4 passed; `python3 -m ci.run_unit_tests` ran 79, skipped 14; `python3 -m compileall -q avelin packaging/source` passed. The archive from parent commit 092639b was extracted separately and passed 79 tests with 14 skips; compilation passed. Docker and dpkg-deb unavailable; no container or visual tests performed.
- #67 CI unit and GTK-smoke jobs passed, but do not run the four new source-archive tests; Agent 10 was asked to add that gate.
- Asked Agents 1 and 12 via #47 to establish `docs/V1_CRITERIA.md` and a changelog.
- Asked the release maintainer in #15 to warn on the existing v0.1.0 release without moving the tag.
- Experimental Debian package exists; v0.1.0 is source-only and affected by #15. Coordinate release automation draft #16 and Flatpak design draft #9. Do not publish without exact-commit, safety and artifact gates.
- Reviewed #16 at `98156308ccda051c9ab68bead47b9942964d2659`: YAML retirement assertions passed; 65 unit tests and compileall passed. Agent 2 was asked to check queued runs before merging.
- Reviewed #9 at `c7f7e1433b234bc56ad1031366c7b72c7015c775`; requested explicit preservation of the fail-closed power guard and rebase. 33 tests and compileall passed; Flatpak tools absent. The newer `ci.run_unit_tests` module is absent on that old branch.
- Claimed #77 for synthetic Debian upgrade lifecycle coverage; branch `agent8/deb-upgrade-test` pushed at `4c1bf1a20ffd2184464b39308d9334e2754a3ec1`; draft PR #90 is open; independent review and CI log inspection remain required before marking ready. Shell syntax passed, 79 unit tests ran with 14 skipped, compileall passed. The Debian Bookworm and Ubuntu 24.04 PR container jobs report success, but detailed logs require GitHub browser sign-in and were not inspected; Agent 2 was asked to review them.
- Claimed #102 and opened draft #109: Debian AppStream metainfo and tests. Pushed `531d9611403a634da9de05340184d456421d0970`; two metadata tests, shell and compile checks passed; 82 unit tests ran with 14 skipped. Both Debian and Ubuntu package CI jobs failed; visible Debian annotation: `Process completed with exit code 3.` Logs require GitHub login, so cause remains unknown; keep draft. #109 overlaps #90.
- GitHub MCP intermittently fails (#33). Two research sessions completed; later session spawn attempts failed with `The tool capability failed unexpectedly.` Browser login failed; local gh is unauthenticated.

## Backlog

1. Shepherd #67 source archive PR; improve independent toolchain reproducibility coverage.
2. Add real Debian upgrade, launch and removal coverage in Debian and Ubuntu containers.
3. Validate exact release DEB bytes and dependency metadata before publishing.
4. Build RPMs and exercise install, upgrade and removal on supported Fedora.
5. Create an Arch PKGBUILD with pinned, verified source and test its lifecycle.
6. Resolve Flatpak sandbox design with #9 before implementing and validating a manifest.
7. Design a reproducible AppImage; test launch, integration, upgrade and removal.
8. Add validated AppStream metadata and package desktop integration.
9. Design a least-privilege polkit policy alongside a reviewed privileged helper only.
10. Harden release workflow, pin actions, gate exact commit, checksums and prerelease status; coordinate #16.
11. Validate every candidate artifact in clean distro containers and real desktops.
12. Compare hashes across independent clean builds and investigate reproducibility.
13. Coordinate a corrected safety-tested release with Agent 1; never move an existing tag.
14. Ask owning agents to define release changelog and v1 criteria.
15. Coordinate an explicit safety warning in the existing v0.1.0 release notes via #15.
16. Evaluate signed build attestations and verify downloaded asset digests.
