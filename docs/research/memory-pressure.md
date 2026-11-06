# Memory pressure: evidence and product guardrails

Research date: 2026-11-06. Scope: read-only, optional system-level memory diagnostics for Avelin. This is a proposal, not an implemented feature or a promise of a speedup. Product idea: [#37](https://github.com/Siradj0-0/avelin/issues/37).

## What the kernel reports

The [kernel PSI documentation](https://docs.kernel.org/accounting/psi.html) describes `/proc/pressure/memory` as a pressure-stall interface. Its `some` line reports the share of time at least some tasks are stalled on memory; its `full` line reports the share of time all non-idle tasks are stalled on memory simultaneously. The `avg10`, `avg60`, and `avg300` fields are percentages over recent 10-, 60-, and 300-second windows. `total` is cumulative stall time in microseconds. These are stall-time observations, not percentages of RAM used.

For context, the kernel describes [`MemAvailable`](https://docs.kernel.org/filesystems/proc.html#meminfo) as an estimate of memory available for starting new applications without swapping. It accounts for reclaimable memory and needed cache; it is not a guarantee that a particular allocation will succeed. PSI and available memory answer different questions and should not be combined into a single unexplained score.

## What this cannot establish

- Pressure alone does not identify a responsible process, prove the cause of a freeze, or predict an out-of-memory event. A short spike does not by itself establish sustained contention.
- An absent, unreadable, malformed, or incomplete interface is **unavailable**, not 0% pressure. A real `0.00` is a measured value and must remain distinguishable.
- System-level PSI describes the scope visible to the running environment. Containers and restrictions require separate validation; do not assert that it describes the entire physical host.
- Do not introduce universal warning thresholds, a memory-clearing action, swap changes, privileged commands, or automatic remediation on the strength of this observation alone. Kernel documentation warns that [dropping caches](https://docs.kernel.org/admin-guide/sysctl/vm.html#drop-caches) can impose substantial I/O and CPU cost when rebuilding them.

## Design and verification proposal

1. Read only `/proc/pressure/memory`; parse named fields rather than assuming their order. Show `some` and `full` separately with their time window and a short explanation. Avoid relying only on color.
2. Use a bounded, nonblocking collection path suitable for the dashboard. No PSI trigger registration is needed: the [kernel trigger interface](https://docs.kernel.org/accounting/psi.html) requires writing a threshold, which this proposal does not do.
3. Unit-test valid values, genuine zero, missing files, denied access, missing fields, malformed values, and out-of-range inputs. Preserve partial/unavailable state rather than inventing readings.
4. Compare the display with the kernel file on a PSI-capable Linux system and validate graceful behavior where PSI is unavailable. Record distro, kernel, environment and limitations. Tests must not intentionally stress a user's machine or alter swap, sysctls, processes, or caches.
5. Coordinate dashboard implementation and accessibility review with Agent 7. Measure whether collection meaningfully affects the app's own overhead before selecting a sampling interval; do not claim a gain without measurements.
