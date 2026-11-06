# Boot timing: evidence and comparison guardrails

Research date: 2026-11-06. This note informs ideas [#39](https://github.com/Siradj0-0/avelin/issues/39) and [#42](https://github.com/Siradj0-0/avelin/issues/42). It describes a possible read-only diagnostic, not an implemented feature or a speedup claim.

## Know what is measured

[`systemd-analyze time`](https://man7.org/linux/man-pages/man1/systemd-analyze.1.html) reports available kernel, initrd and userspace phases. Its finish point is when system services have been spawned, not necessarily when every service finishes initialization, storage becomes idle, or a graphical desktop is ready. Available phases depend on the environment; missing phases must not be treated as zero. Systems without an accessible systemd manager need an explicit unavailable state.

The same manual says `blame` can be misleading when services wait on other services; it omits some activation types and queue waits. `critical-chain` also has limitations involving parallelism, socket activation, units without an activating state and jobs such as timed-out jobs. A chain is an investigative clue, not proof that a named unit caused a slow boot. Plot data may instead reflect a unit's most recent start and omit unloaded units. Do not rank services as safe to disable from these observations.

[`journalctl --list-boots`](https://man7.org/linux/man-pages/man1/journalctl.1.html) lists boot identifiers and the timestamps of the first and last journal messages for each boot. Those are not authoritative measurements of startup duration and must not be used as a substitute for boot timing.

## Compare carefully

- If a user explicitly saves snapshots, compare the same phase and units. Show the values, absolute difference, sample count and context; a percentage needs a nonzero baseline. Keep missing values unavailable.
- [The systemd ID API](https://www.freedesktop.org/software/systemd/man/latest/sd_id128_get_machine.html) describes the kernel boot ID as unique per running kernel instance. Use it to avoid counting repeat observations from one boot as independent boots, if available. Treat identifiers as sensitive; default to local storage and never automatically upload them.
- A single before/after pair is observational. Kernel and software updates, power conditions, workload and other changes can confound a comparison. For multiple distinct boots, show a simple summary and range alongside the sample count, and warn about mismatched context rather than claiming causation.
- Collect only on request, keep local history bounded, and provide explicit deletion. Do not reboot, change services, request privilege, clear caches or upload unit names as part of the measurement.

## Verification before integration

Use fixtures for incomplete startup, missing phase values, unsupported environments, malformed or timed-out output, duplicate boot IDs, zero baseline and changed context. Test a 10-second baseline and 8-second comparison as −2 seconds and −20%. Separately check actual versions and permissions on representative systems; do not label fixture tests as real-distro or desktop-readiness testing. Coordinate any dashboard work with Agent 7.
