# Undo journal prototype

This standalone prototype implements **journal file operations only**. It is not connected to `app.py`, `actions.py`, PR #3, a UI, D-Bus, GSettings, power profiles, or any system write. It does not locate a home or state directory, create a journal directory, run commands, change settings, or automatically recover anything. Tests use newly created temporary directories and simulated records only. Do not ship or wire this prototype to real changes without the integration work below.

## Supported record and state machine

One private directory holds at most **one** unresolved record. Version 1 accepts exactly six JSON fields: integer `version` (1), random 32-character lowercase hex `transaction`, `setting`, `previous`, `user_value`, and `state`. Input is UTF-8, bounded to 4096 bytes, with duplicate/unknown fields, unknown versions, invalid types, nonstandard JSON, unknown states and values rejected. Only changed snapshots are allowed:

- `gnome-animations`: prior effective value `true`; `user_value` is `true` or `null` (no explicit user override). Target is implicitly `false`. Other combinations fail closed, including unusual override/effective combinations the prototype cannot faithfully represent.
- `power-performance`: prior profile `balanced` or `power-saver`; `user_value` is `null`. Target is implicitly `performance`.

There are no arbitrary keys, values, file paths or commands in the record. An unchanged/no-op request must not be journaled or mutated. The transaction ID prevents accidental stale-session updates; it is **not** authentication or proof that the setting changed.

The only normal transitions are:

```text
prepared -> applying -> verified -> restoring -> restored
```

`recovery()` only classifies the stored state; it never checks or changes the actual setting. `prepared` means no write was started **if the future caller obeyed the protocol**. `applying` and `restoring` mean the external operation may or may not have occurred; never silently retry or undo. `verified` means a caller recorded success, not that the value is still current. `restored` means a caller recorded successful restoration, not that another actor has not subsequently changed it. A different or unavailable current value requires review, not forced restoration.

Under the same held lock, `resolve_uncertain()` records an **explicit operator-reviewed** outcome after independent inspection: `applying` can resolve to `prepared` (`not-applied`) or `verified` (`applied`); `restoring` can resolve to `verified` (`not-restored`) or `restored` (`restored`). The method cannot inspect the real setting, prove the conclusion or close a race with another actor. If the outcome cannot be determined, leave the record unresolved; there is deliberately no force-discard for these states. Only `prepared` and `restored` records can be explicitly discarded. Corrupt records are never automatically overwritten or deleted.

## Proposed protocol for a future integration

The following is a contract, **not implemented settings integration**:

1. Probe capability and get informed user consent. Capture a valid snapshot; choose an explicitly configured, existing, user-owned mode-0700 directory. If a journal already exists, recover or report it rather than overwriting it.
2. Acquire `Journal(directory).locked()` and keep that same session and lock throughout the full operation. Persist `prepared`; persist `applying` and require successful return **before** calling any external write. If recording or syncing fails, do not write the setting.
3. Recheck external state and permissions immediately before the write. Perform only the separately reviewed, allowlisted operation. Verify the result; only then persist `verified`. Any timeout, exception or lost process leaves `applying` uncertain. The journal cannot make checks and external writes atomic.
4. On explicit undo, reacquire the lock, inspect and compare the current value with the applied value, and check capabilities again. Persist `restoring` **before** the external restore; independently verify its result before persisting `restored`. Refuse conflicts. If an operation is uncertain, preserve the record and require review; do not auto-undo on startup.
5. After `restored` is confirmed, the user may discard the record. A never-started `prepared` transaction can also be discarded. If a write failed after rename/unlink or during directory sync, `DurabilityUncertain` poisons the session. Close it, reopen and inspect; visibility after an error is not proof of durable commit. Before any later external write, perform a successful journal transition and sync again, or stop if uncertainty cannot be resolved.

A future UI must own confirmation, secure directory provisioning, startup recovery, user-visible errors, concurrency, accessibility and conflict handling. It must coordinate with the existing controls so that only one component manages a setting. A per-user lock cannot serialize other users, desktop apps or system-wide power controls. Changes away and back to the same value are indistinguishable.

**Power-profile limitation:** a snapshot stores only the previously effective profile, not daemon holds. A manual switch can cancel holds; restoring a prior profile does not recreate them. Before any power write, a future integration must detect and decline active holds, handle inability to query them as unavailable, and document/test the remaining race where a hold appears after the check. The journal alone does not make this operation fully reversible. [Power Profiles daemon API](https://upower.pages.freedesktop.org/power-profiles-daemon/gdbus-org.freedesktop.UPower.PowerProfiles.html).

## Filesystem and trust model

The caller supplies an absolute path to an **existing** private directory. Each component is opened relative to an already-open directory descriptor with `O_DIRECTORY|O_NOFOLLOW`; `.`/`..`, empty components and relative paths are rejected. The final directory must be owned by the effective user and mode 0700. Journal and lock files must be singly linked regular files owned by that user and mode 0600; lock and data symlinks, hard links and special files are rejected. Opens are nonblocking where applicable. The lock is an exclusive nonblocking `flock`, held through the caller's session; lock-file identity is rechecked. A cooperative second process receives `Busy`. A session belongs to the creating process and thread; calls from another thread or a forked child and reentrant calls are rejected. Keep session creation, use and exit on that owner thread. Lock descriptors can still be inherited across `fork` even though the inherited session cannot be used; a future caller must prevent children from retaining them, or the lock can outlive the parent. `O_CLOEXEC` addresses `exec`, not `fork`.

A new, exclusive random temporary file in the same directory is written completely and file-synced, then atomically replaced into place using directory-relative descriptors, followed by a directory `fsync`. `discard` unlinks and syncs the directory. Errors before replacement leave the old journal. From just before replacement or unlink until directory sync succeeds, the session is marked uncertain; an `OSError` becomes `DurabilityUncertain`, while interruptions such as `KeyboardInterrupt` propagate and leave the session poisoned. A crash may leave an orphan temporary file; the prototype does not automatically remove unrelated or orphan files. `flock` is advisory, not a security boundary. [Linux open](https://man7.org/linux/man-pages/man2/open.2.html), [flock](https://man7.org/linux/man-pages/man2/flock.2.html), [fsync](https://man7.org/linux/man-pages/man2/fsync.2.html), [Python `os.replace`](https://docs.python.org/3/library/os.html#os.replace).

This is a **cooperating-process** design, not protection against root, a hostile process with the same UID, malicious replacement or rename of parent directories, broken filesystem semantics, unusual ACLs, compromised Python, or malicious storage. Protect the directory and its ancestors. Network/FUSE/overlay filesystems, storage firmware and filesystems that do not honor required locks, atomic rename or sync semantics are not validated. The record is not authenticated, encrypted, host-bound or protected against rollback/tampering. Do not trust it as authority to modify settings; validate current state and user intent. Mode checks are not a complete ACL audit.

The prototype depends on Linux and Python's descriptor-relative APIs, `O_NOFOLLOW`, `O_DIRECTORY`, `flock` and directory `fsync`; unsupported or failing operations must fail closed. The exact behavior on real distributions and power loss is unverified. It deliberately does not create the future state directory: the [XDG Base Directory specification](https://specifications.freedesktop.org/basedir/latest/) identifies `$XDG_STATE_HOME` for persistent state, but provisioning, sandbox compatibility and migration remain integration work.

## Tests and remaining work

The tests use temporary directories and fake state only. They exercise schema and size rejection, duplicate JSON, symlinks and ancestor links, hard links, FIFOs, permissions, lock replacement, subprocess contention, shared-session threads, inherited forked sessions and reentrancy, stale transitions, injected write/fsync/rename failures and interrupts, late rename failure, crash after recording `applying`/`restoring`, recovery outcomes and session poisoning. These tests do **not** simulate real power loss, hostile same-user races, ACLs, network filesystems or real settings. Before shipping, add filesystem fault-injection and real-distro tests; a power-hold capability check; secure directory provisioning; UI integration and manual recovery review; and a security review of the complete caller protocol.
