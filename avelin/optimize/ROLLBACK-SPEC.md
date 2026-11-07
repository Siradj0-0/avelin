# Conflict-aware rollback specification

Status: **design only**. This does not implement a journal, settings access,
authorization, application or restoration. A snapshot is not proof that Avelin
changed a setting or permission to change it. The existing prototype in [PR
#8](https://github.com/Siradj0-0/avelin/pull/8) is separate and requires a
high-risk split and independent review before integration.

## Scope and prerequisites

- Each operation is optional and separately confirmed after a preview showing
  the actual target, current and proposed values, effect, risks, persistence,
  expected recovery, and limitations. Advanced actions require explicit opt-in.
- A narrow, independently reviewed authorization boundary must allowlist typed
  actions and validate parameters; no generic root command or arbitrary shell.
  Do not install packages or perform privileged changes without confirmation.
- An operation is eligible for restoration only if its exact validated prior
  state, target identity and context were captured, a durable transaction record
  identifies this operation, and the write and subsequent verification were
  recorded successfully. A prepared snapshot or matching value alone is not
  evidence that a write occurred. A no-op must not create an undo operation.
- A checked, private journal location, safe file handling, concurrency model
  and recovery UX must be designed and reviewed before real operations. A
  journal is not authenticated proof of external state or protection from
  other programs or same-user tampering.

## Transaction boundaries

A future implementation must retain a suitably scoped lock through each
journal transition and its associated external operation. Its minimum phases
are:

1. **Prepared:** validate applicability, permissions, user intent, prior state,
   exact target and recovery information. Persist and sync this record before
   any write. If it is a no-op, leave the setting untouched.
2. **Applying:** recheck current state and capability; durably mark the write as
   about to begin before invoking the action. A timeout or crash may mean the
   write did or did not happen. Do not infer the outcome from current value.
3. **Verified:** read back the external result and persist verification only
   after it matches the intended state. A failed readback is not a successful
   write and must remain visibly uncertain pending review.
4. **Restoring:** require a separate user request; revalidate identity, context,
   permissions and transaction evidence, then compare current state with the
   state Avelin last verified. Detectable drift is a conflict, not permission to
   overwrite. Durably mark restore as starting before the restore operation.
5. **Restored:** independently read back and verify the intended restoration;
   record success durably before clearing or resolving recovery information.
   A failure or interruption during restore remains uncertain and needs review.

A failed or uncertain journal commit must prevent further external writes in
that session. Seeing a file after a failed sync does not prove durability; a
future implementation must reopen, inspect, resolve and successfully persist
and sync the next transition before proceeding. File sync and directory sync
serve different purposes, and actual crash durability depends on filesystem and
storage semantics: [fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html).
Never silently discard unresolved recovery records.

## Conflicts and limits

- A current value equal to Avelin's target does not prove that no other actor
  changed it, including a change away and back. A per-user lock does not lock
  other desktop applications, users or system services. Checks followed by
  writes are not atomic unless the specific backend supplies and uses an
  appropriate conditional operation. Communicate this residual race; do not
  promise perfect conflict detection or claim verified ownership of the value.
- If the source, target identity, desktop/session, capability, value or required
  authorization is missing, changed, ambiguous or inaccessible, refuse the
  restore and explain what is known. Never replace unknown readings with zero,
  invent prior values, or automatically retry an uncertain operation.
- Preview the proposed recovery and limitations again before an explicit user
  decision. If safe restoration cannot be established, offer an explanation and
  manual recovery guidance rather than an overwrite. Restoring configuration is
  not equivalent to recovering deleted data, processes, or other actors' state.
- Power-profile writes remain disabled under [issue #15](https://github.com/Siradj0-0/avelin/issues/15):
  manual profile switches can cancel another application's holds; switching
  back does not recreate them, and a pre-write check cannot remove the race.
  See the [power-profiles daemon API](https://upower.pages.freedesktop.org/power-profiles-daemon/gdbus-org.freedesktop.UPower.PowerProfiles.html).

## GSettings Boolean example

Capture the effective Boolean and whether a user override exists, including its
exact Boolean value when present. An absent override is not an explicit false
value: [get_user_value](https://docs.gtk.org/gio/method.Settings.get_user_value.html).
If restoration eventually receives approval, preserving an absent override
would require a reset rather than writing the old effective value:
[reset](https://docs.gtk.org/gio/method.Settings.reset.html). A reset exposes
current defaults or policy, which may have changed; the original effective
value is not guaranteed. Report that result honestly and verify both the user
override state and effective value. An inconsistency or unavailable observation
requires review, not a blind second write.

## Required validation before implementation ships

- Unit tests: absent versus false/true override, no-op, unsupported capability,
  denied authorization, changed values, malformed snapshot, stale identity,
  partial write, failed verification and refused restore.
- Fault-injection tests: process exit before and after each durable phase;
  file and directory sync errors, rename/unlink uncertainty, and failure
  during restore. Assert that no external operation follows an unsuccessful
  journal transition and that uncertainty survives restart for user review.
- Concurrency tests: other applications or controls writing between read and
  write, changes away and back, multiple users, and same-value ambiguity.
  Tests must expose—not claim to eliminate—races without backend atomicity.
- Disposable real-distro tests for supported backends, permissions, changed
  defaults, reboot, recovery and accessibility, plus documented stop conditions.
  Real power-loss behavior is not established by mocked fsync tests.
- High-risk restore/undo or privileged changes need two independent agent
  reviews and QA evidence. No agent merges its own PR.
