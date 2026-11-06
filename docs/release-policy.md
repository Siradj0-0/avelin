# Release and quality policy

Avelin changes system preferences and can permanently empty trash. Safety and clear limitations matter more than a version number. A GitHub prerelease is not evidence of broad compatibility.

## Before any preview release

1. Define the exact commit, version, changes and known limitations. Never reuse an existing tag for different code.
2. Run the full unit and integration suite for the actual release commit; inspect CI results rather than assuming a workflow passed.
3. For each distributed package, build and exercise that exact artifact in a clean environment, inspect its contents and dependencies, and verify installation, launch, update/upgrade where applicable, and removal. A source-only preview must say it has no installers.
4. Review destructive and privileged changes for narrow scope, explicit consent, truthful error handling, recovery, and safe behavior on unavailable capability. No silent deletion or broad shell execution.
5. Publish accurate release notes with limitations and recovery instructions; mark incomplete previews as prereleases. Do not promise a platform or hardware works solely because one smoke test passes.
6. Review artifact integrity and provenance before publishing binaries. Do not implement self-update until the distribution-specific trust and installation model is reviewed and tested.

## Before considering v1.0.0

Establish and document a supported distribution, desktop and hardware matrix. Test the native GUI visually, by keyboard and with assistive technology; test storage, hardware, power settings, rollback and error paths on actual supported systems; add security review, real package upgrade/removal tests, translations and support documentation. Test failures and regressions must be triaged rather than masked. No release can guarantee correctness on every machine.

## Report problems

Use the repository's issue forms. Sanitize screenshots and logs first; never post credentials or private files. Report security vulnerabilities privately as described in [SECURITY.md](../SECURITY.md).
