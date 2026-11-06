# Optimization backend catalog

This is an **experimental backend only**. It is not wired into the GTK app, does not change anything automatically, and does not supersede the existing controls in `actions.py`. Both supported operations correspond to capabilities Avelin already exposes; this module adds explicit snapshots, stale-state checks and guarded restoration, not a promise of new speedups. Changes are opt-in, one at a time, and persist until explicitly reversed or changed elsewhere. No root helper, automatic deletion, kernel tuning, service disabling, or broad commands are provided.

## Catalog

| ID | Opt-in change and detection | Scope and possible benefit | Risks and limits |
| --- | --- | --- | --- |
| `gnome-animations` | Set `org.gnome.desktop.interface` `enable-animations` to `false`, only on Linux in a GNOME session with PyGObject/Gio, the boolean schema key, and write permission. | GNOME user setting for the current account/session; other users are not intentionally changed. GNOME describes this as a global desktop key affecting the window manager and panel. Less animation work and potentially snappier perceived transitions; **no guaranteed throughput gain**. | Visual transitions disappear; accessibility or personal preferences may be affected. Some applications/desktops may ignore it. An existing override is restored, or reset if none existed. Reset follows the **current** administrator/schema default, which can differ from the original effective value. |
| `power-performance` | Select `performance` only when `powerprofilesctl list` advertises it and `get` returns a recognized advertised profile. | **System-wide**, shared with other users; potentially higher performance on supported hardware. | Greater power draw, heat and fan noise, shorter battery life; speedup is workload/hardware-dependent and may be degraded by temperature or other constraints. Service authorization or policy may reject changes; profile holds, other apps or users may change it. Not available on all hardware. Restores the captured profile if still advertised. |

Detection is conservative: absent PyGObject, schema/key, permissions, executable, service, recognized profile or GNOME session means unavailable, not success. No fallback assumes GNOME on another desktop. The daemon may perform its own authorized system-wide operations; Avelin itself does not call sudo, pkexec, a shell, or write sysfs. Commands are limited to `powerprofilesctl list`, `get`, and `set` with exactly `power-saver`, `balanced` or `performance`; a normal trusted executable search path is assumed. Timeouts and nonzero exit statuses are errors. GSettings uses a fixed schema and key through Gio, not arbitrary commands.

## Integration contract

The app must explicitly present benefit, risk, scope and restoration information and obtain informed user confirmation before calling `apply`. A minimal prospective flow:

```python
from avelin import optimizer

# Probe is read-only; handle optimizer.Unavailable and show disabled controls.
snapshot = optimizer.prepare(optimizer.ANIMATIONS)
# Keep snapshot before attempting a write, including if apply raises.
# After user confirmation:
optimizer.apply(snapshot)
# Later, after user explicitly requests undo:
optimizer.restore(snapshot)
```

`prepare` captures the effective state and, for GSettings, whether a user override existed. `apply` rechecks that state before writing and verifies the result. If already at the target, it makes no write and the snapshot records a no-op. `restore` refuses to overwrite if the current value no longer looks like the value Avelin applied, and verifies the restored state. A `Conflict` means state changed; prompt the user to review instead of forcing it. `Unavailable` means capability, write, or verification failed; do not claim success. Both exceptions are `RuntimeError` subclasses. Invalid IDs and malformed snapshots raise `ValueError`.

**Keep the snapshot before applying**, even if an error or timeout occurs: a write can have succeeded before the error. The caller is responsible for preserving the snapshot securely and presenting recovery after process exit/crash; this backend has no persistent journal or automatic rollback. Use the same account and desktop context to restore. Snapshots are not authentication or proof of ownership and must not be accepted from untrusted sources. Recovery may fail if policy, permission, the desktop, hardware or service changes. If no snapshot survives, use the desktop's own settings or `powerprofilesctl` to choose the desired profile; for GNOME use its settings UI or the appropriate `gsettings set/reset` command. Do not assume the prior profile or override.

The checks are best-effort, not atomic compare-and-swap: another actor may change a value between checking and writing, or change it away and back to the same value undetectably. A daemon profile hold may also alter the effective value immediately afterward. A snapshot retained from a failed operation should only be restored after reviewing the actual state; if a change never took effect, restore can raise `Conflict`. There is no forced overwrite mode. A no-op snapshot intentionally cannot undo later third-party changes.

Before shipping a UI integration, reconcile the existing `actions.py` controls with this backend rather than having two conflicting state managers; define secure snapshot storage/lifetime, per-user consent and cross-user warnings, display failures and recovery, and test on real GNOME versions, daemon versions, hardware, authorization policies, and concurrent profile changes. Tests here use fakes and do not establish real-distro, Polkit, thermal, power, or performance behavior.

## Sources

- GNOME upstream schema, `enable-animations` description: <https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/raw/main/schemas/org.gnome.desktop.interface.gschema.xml.in>
- GLib Gio user overrides and reset semantics: <https://docs.gtk.org/gio/method.Settings.get_user_value.html>, <https://docs.gtk.org/gio/method.Settings.reset.html>, and <https://docs.gtk.org/gio/method.Settings.is_writable.html>.
- Power Profiles daemon upstream API, available profiles, holds and degradation: <https://upower.pages.freedesktop.org/power-profiles-daemon/gdbus-org.freedesktop.UPower.PowerProfiles.html>.
- `powerprofilesctl` command reference: <https://manpages.debian.org/trixie/power-profiles-daemon/powerprofilesctl.1.en.html>.
