# Read-only hardware monitoring backend

`avelin.hardware.HardwareMonitor` is a standalone Linux backend. No UI is wired to it: integration into `app.py` is still required. It does not run commands, invoke a shell, open device nodes, request privileges, modify hardware, or require extra packages. It reads the current process's sysfs view; it cannot guarantee access to or visibility of the host's devices.

## API

Create one `HardwareMonitor()` and call `sample()` periodically, serially, using the same instance. A `Snapshot` contains `storage` and `gpus` tuples, enumeration statuses `storage_status` and `gpu_status`, a `sandbox` marker and a monotonic timestamp. Each measurement is a `Reading(value, status, source)`; only `ok` has a value. The source is the exact path in the configured sysfs tree. Empty inventory with `ok` means only that no entries were visible, not that the machine has no hardware. A partially disappeared GPU makes enumeration `unavailable` while preserving other detected GPUs.

Statuses: `ok`; `unavailable` (not exposed, unsupported, or other I/O failure); `permission` (EACCES/EPERM); `sandbox` (a path was missing in a positively identified Flatpak or Snap); `invalid` (malformed/out-of-range data, invalid interval); `warming_up` (first sample or changed device identity); and `counter_reset` (counter went backwards). Permission errors take precedence over sandbox. Missing paths in a sandbox are only a *possible* visibility restriction, not proof that a host device exists. The `sandbox` flag recognizes `FLATPAK_ID`, `SNAP`, or `/.flatpak-info`; it does not detect every container, namespace, permission policy, or sandbox, and a false flag does not imply host access. Device hotplug and races may yield partial results. Sysfs and root paths, environment and clock can be injected for tests.

## Storage

Enumerates `/sys/block` whole block devices as visible, including virtual devices (loop, device mapper, RAM and zram); does not present partitions as disks, nor assume every entry is a physical disk. `dev` is the kernel major:minor; `device/model` is optional; `size` is in 512-byte sectors and is converted to bytes; `queue/rotational` is the kernel's 0/1 flag, not an infallible SSD/HDD classifier. These fields can independently be unavailable. Missing removable media can legitimately report zero size.

Busy percent is **not capacity used or throughput**: it is the delta of field 10 (`io_ticks`, milliseconds with I/O queued) in `/sys/block/<name>/stat` divided by elapsed monotonic milliseconds, multiplied by 100. Two valid samples are required and `queue/iostats` must explicitly report 1 in both samples; disabled or unreadable accounting is never treated as idle. Identity combines major:minor, resolved sysfs path and `diskseq` when exposed. This reduces, but on older kernels without diskseq cannot eliminate, ambiguity from rapid hotplug and reuse. Disappearing entries, unreadable counters, changed identity and counter resets are never bridged. Invalid intervals or a delta over 100% return `invalid`, not a clamped or invented reading. Kernel accounting is an approximation, can undercount concurrent I/O on modern kernels, and is not a direct measure of saturation. Stacked devices can double count; do not sum device percentages.

## GPUs and iGPUs

Enumerates DRM `cardN` devices in `/sys/class/drm`, deduplicated by resolved device, ignoring connector and render nodes. Vendor/device IDs and kernel driver are raw sysfs attributes; vendor IDs do not reliably establish integrated versus discrete, so `kind` is deliberately unavailable for all devices. DRM-less devices, some virtual devices and devices hidden from the current environment may not appear. For the `amdgpu` driver only, reads the driver's documented `gpu_busy_percent` and accepts integers from 0 to 100; the driver's SMU reports aggregate IP activity. Missing, inaccessible or malformed attributes remain non-values. Intel, NVIDIA, other drivers and non-DRM devices have no fabricated percentage. Per-process DRM fdinfo engine timings are not equivalent to a universal per-device GPU percentage and are not aggregated here. No external proprietary utility, elevated helper or device probing is used.

## Authoritative references

- Linux kernel block statistics, `io_ticks` and 512-byte sector definition: https://docs.kernel.org/block/stat.html
- Linux kernel I/O statistics, including accounting caveats: https://docs.kernel.org/admin-guide/iostats.html
- Linux kernel sysfs ABI (`/sys/block/*/size`, `dev`, `diskseq`, `queue/rotational`): https://github.com/torvalds/linux/blob/master/Documentation/ABI/stable/sysfs-block
- Linux DRM sysfs device structure: https://docs.kernel.org/gpu/drm-internals.html
- Linux amdgpu `gpu_busy_percent`: https://docs.kernel.org/gpu/amdgpu/thermal.html#gpu-sysfs-power-state-interfaces
- Linux DRM client fdinfo statistics and their per-client/engine scope: https://docs.kernel.org/gpu/drm-usage-stats.html

Run `python3 -m unittest discover -s tests -v`. Tests use synthetic trees, not real GPU hardware; distribution and hardware validation is still needed.
