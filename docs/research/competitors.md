# Linux tuner and cleaner comparison

Research snapshot: 2026-11-06. This compares documented capabilities with Avelin main at `da63804`; it is not an exhaustive feature audit or proof that another product lacks an unmentioned feature. Findings identify Avelin backlog gaps, not claims of competitor deficiencies or measured performance improvements.

## What existing tools establish

| Tool | Documented capability | Implication for Avelin |
| --- | --- | --- |
| [BleachBit](https://www.bleachbit.org/features) | Descriptions, selection and preview precede deletion; it has cleaners for multiple applications and package managers. | Avelin's bounded location scan does not preview proposed deletions; scope and freshness for any future action need explicit design ([#85](https://github.com/Siradj0-0/avelin/issues/85), [#55](https://github.com/Siradj0-0/avelin/issues/55)). Do not treat a directory estimate as a reclaimable total or copy cleaners without individual review. |
| [Stacer](https://github.com/oguzhaninan/Stacer) | Its upstream README describes system optimization and monitoring and explicitly says the project is abandoned, with no further releases. | Maintenance continuity matters; this status alone does not establish which features work on current distributions or demand a clone. |
| [TLP](https://linrunner.de/tlp/introduction.html) | Laptop-power profiles apply configurable settings on system events. Version 1.9 introduced three profiles and `tlp-pd`; version 1.10 permits arbitrary AC/battery profile assignment. | Avelin only discovers power profiles; its writes are blocked because holds may be cancelled ([#15](https://github.com/Siradj0-0/avelin/issues/15)). Investigate conflicting managers ([#107](https://github.com/Siradj0-0/avelin/issues/107)); do not assert all TLP versions conflict or apply any settings automatically. |
| [GNOME System Monitor](https://apps.gnome.org/SystemMonitor/) | Process management, resource graphs and a file-system view are documented. | Avelin's dashboard already graphs CPU and RAM but lacks an on-demand visible-process memory snapshot ([#44](https://github.com/Siradj0-0/avelin/issues/44)). Such a snapshot must be bounded and privacy-preserving, not an automatic process killer. |
| [GNOME Disk Usage Analyzer](https://help.gnome.org/baobab/index.html) | Scans home, local and remote folders and displays storage graphs. | Avelin estimates selected locations and displays root capacity, but does not present the proposed home/root filesystem space and inode check ([#36](https://github.com/Siradj0-0/avelin/issues/36)). A scan and filesystem availability are different measurements; this is not a claim that Baobab provides inode health. |
| [KDE Plasma System Monitor](https://apps.kde.org/plasma-systemmonitor/) | Exposes sensors, processes and other system resources. | The broad monitoring category is already served; justify Avelin additions through low-overhead, understandable, optional observations ([#37](https://github.com/Siradj0-0/avelin/issues/37), [#38](https://github.com/Siradj0-0/avelin/issues/38)), not a claim that KDE lacks them. |

Avelin's current behavior and boundaries are documented in its [README](../../README.md), [roadmap](../research-and-roadmap.md) and [storage safety notes](../storage-safety.md). Filesystem available space is not the sum of location estimates; snapshots, quotas and shared storage complicate recovery.

## Research priorities and guardrails

1. **Storage truthfulness:** #36 and #85 address different questions: available filesystem capacity versus the scope of a proposed action. No new deletion is implied.
2. **Pressure and overhead:** #37 explains kernel memory-pressure stalls; #38 investigates monitoring overhead. Validate on constrained hardware; neither is a proven speedup.
3. **Boot and startup:** [#39](https://github.com/Siradj0-0/avelin/issues/39), [#40](https://github.com/Siradj0-0/avelin/issues/40) and [#42](https://github.com/Siradj0-0/avelin/issues/42) explore opt-in measurements and read-only explanations. Competitor coverage was not established here.
4. **Power coordination:** #107 is guidance only. Do not change a profile, a service or a kernel parameter as a side effect of detecting another manager.

Avoid blanket “clean all” actions, service disabling, force-kill buttons and promised speedups. Assess actual user needs and maintainability before duplicating existing utilities. Sources above describe functionality, not user demand or evidence of effectiveness; test those separately.
