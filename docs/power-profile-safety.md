# Power-profile safety

Avelin discovers profiles using `powerprofilesctl list` and `powerprofilesctl get`. It currently does not issue `powerprofilesctl set`: selecting the observed current profile is a read-only no-op; selecting a different profile returns an explanation instead. Profile discovery may be unavailable, and a read is only a snapshot: other software can change the profile at any time.

A manual profile change can cancel active power-profile holds belonging to other applications. Switching back to the previous value does not recreate those holds. An `ActiveProfileHolds` read followed by a profile write is not atomic; a new hold can appear between them. The documented API does not provide a conditional hold-check-and-set. Blocking all actual changes avoids Avelin initiating that race, including when hold detection is unavailable. This also blocks changes when no hold exists, a deliberate temporary loss of functionality.

The existing confirmation dialog may still offer a change and suggest switching back; the backend will reject an actual change. The dialog needs a follow-up update. Re-enabling changes requires a reviewed consent and recovery design, accurate UI warnings, a compatible way to identify the daemon and detect holds, and recognition of the remaining race. No claim is made about other software's actions, daemon behavior on every distribution, or a user's ability to restore another application's hold.

Reference: [power-profiles-daemon D-Bus API: holds and ActiveProfile](https://upower.pages.freedesktop.org/power-profiles-daemon/gdbus-org.freedesktop.UPower.PowerProfiles.html).
