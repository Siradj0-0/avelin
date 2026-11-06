# v1.0.0 release criteria

Avelin must not publish v1.0.0 until every applicable gate below is met and its evidence is reviewed. An unchecked item is not a claim of readiness. A maintainer must decide the supported scope; no distribution, desktop, hardware or package format is supported merely because it appears in a test example.

## Release record

- [ ] Record the exact release commit, version, tag, date and decision makers. The tag must identify the reviewed commit and must not be reused for different code.
- [ ] Publish a maintainer-approved support matrix covering distro and version, architecture, desktop/session, Python version, hardware classes and package formats. Identify unsupported or untested combinations and how users obtain help.
- [ ] Link each gate to dated evidence, exact commit or artifact, environment, result and reviewer. Resolve failed checks and release-blocking issues; record limitations in release notes. Do not silently waive a gate.

## Safety and recovery

- [ ] Each action has a truthful dry-run preview, clear scope and explicit confirmation. No silent deletion or privileged commands; privileged operations use a narrowly scoped polkit helper.
- [ ] Each optimization is reversible with tested restoration or explicitly identified as irreversible with a warning. Advanced opt-in is required for risky or major changes, including desktop changes, zram and kernel parameters. Confirm any package installation and use only approved trusted sources.
- [ ] Test denied permission, missing tools, timeout, partial failure, external changes and recovery. Never represent an unavailable measurement as zero. Distinguish partial storage estimates from recoverable space.
- [ ] For empty-trash behavior, test confirmation and scope, plus user-visible partial-deletion warnings for timeouts, failure and malformed output, including real `gio` and mounted-volume cases in disposable environments. Track [issue #24](https://github.com/Siradj0-0/avelin/issues/24).
- [ ] Resolve [issue #15](https://github.com/Siradj0-0/avelin/issues/15) for the intended release, or keep power-profile changes disabled across every apply and restore entry point. Test the guard against cancellation of another application's holds. A fix on main does not change an already published release.
- [ ] Complete security and architecture reviews of privileged operations, deletion, rollback, update trust and cross-module boundaries. Resolve release-blocking findings and document recovery instructions.

## Function and quality

- [ ] Run the full nonempty automated test suite and syntax/compile checks on the exact release commit. Investigate failures and skips; run GTK integration tests under Xvfb or an equivalent headless display rather than counting skipped tests as passes.
- [ ] Exercise every supported matrix combination on representative real systems, including detection, dashboard readings, settings, storage, update and recovery paths. Test malformed and missing data, unsupported hardware and permission failures.
- [ ] Separately perform real visual, keyboard-only, screen-reader, contrast and scaling checks on supported desktops. Record environments and results; a headless smoke test alone is not visual or accessibility validation.
- [ ] Provide current user, installation, recovery, security-reporting and contributor documentation and the translations required by the approved support scope.

## Distribution and update

- [ ] Build installable artifacts for each approved release format from the release commit; inspect contents, dependencies and provenance. In clean representative environments, test installation, launch outside the checkout, upgrade and removal of the exact artifacts.
- [ ] Publish a real GitHub Release for the v1.0.0 tag with accurate notes, attached installable artifacts and checksums. Validate that notes, tag, commit and artifacts correspond.
- [ ] Demonstrate a reviewed, trustworthy update path for every shipped format, including authenticity and installation behavior. An informational release check alone is not a self-update implementation.
- [ ] Verify that release automation fails closed on errors and cannot publish without authorization; review the exact-commit CI and artifact evidence before publication.

See [release policy](release-policy.md), [research and roadmap](research-and-roadmap.md), [storage safety](storage-safety.md) and [update security](update-security.md) for current limits and supporting context.
