# UI review checklist

Use this checklist for Avelin's shell and non-dashboard pages. Record what was actually exercised; a test plan, a screenshot file, and a successful smoke test are not proof of a complete visual or accessibility review. Do not include personal data, credentials, machine identifiers or private file names in committed screenshots or logs. Use a disposable test account with representative dummy data.

## Record the environment

- Commit and branch, date, distribution, desktop session, GTK version, display backend, theme, window size, display scale and text scale.
- Page and state, test result, observed issue and reproduction steps. Mark untested items explicitly; do not infer a pass from a missing failure.
- Screenshot filename and resolution when applicable. Capture under Xvfb or GTK Broadway, open each image and inspect it at the intended size before committing it under `docs/screenshots/`. Record any clipping, overlap, unreachable controls or unreadable text and fix before calling it passed.

## Automated baseline

Use distribution Python with GTK 4, PyGObject, cairo and a display; follow [source setup](../source-setup.md) for installation and prerequisites. Do not install packages without the user's confirmation. From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q avelin
xvfb-run -a /usr/bin/python3 -m tests.gui_smoke
AVELIN_REQUIRE_GTK=1 xvfb-run -a /usr/bin/python3 -m unittest tests.test_ui_accessibility -v
```

Record output and exit status. The smoke test constructs and closes a window; it does **not** capture or inspect screenshots. The strict UI test must run rather than skip. These checks do not replace real-desktop, keyboard or screen-reader review.

## Views and states

- **Navigation:** each non-dashboard destination, initial focus, selected destination, back-and-forth transitions and a narrow or tiled window. Never change the dashboard while reviewing the shell.
- **Preferences:** supported and unavailable switches, pending changes, successful readback and failed readback. Explain what is changed; avoid implying an exact restore if it is not implemented. Do not make system changes on a real user session without explicit consent.
- **Storage:** before scan, scanning, empty result, partial result and failure. Confirm scans do not imply that measured space is safely reclaimable. Review the irreversible trash confirmation and cancellation without actually deleting a user's files.
- **System and updates:** missing information, failed or pending update check, release available and opening the release page. Do not imply that updates have been installed.
- **Future pages:** when present, cover first-run detection, optimization search/filter/no-results, risk and revert states, settings, About and update prompts. Mark absent features as not implemented rather than passed.

## Size and accessibility matrix

- Inspect at 1366 × 768, 1024 × 600 and a narrow tiled window; repeat key views with large text. All controls and text must remain reachable. GNOME identifies 1024 × 600 as its recommended minimum desktop display size. [GNOME adaptive guidance](https://developer.gnome.org/hig/guidelines/adaptive.html)
- On real GNOME and KDE sessions where available, test high contrast and 100%, 150% and 200% scaling, including moving between displays. These are proposed test cases, not claims of supported platform coverage.
- Use keyboard only: check logical Tab/Shift+Tab order, visible focus distinct from selection, activation, dialog focus, Cancel/Escape and focus return. Essential information must not depend only on hover. [GNOME keyboard guidance](https://developer.gnome.org/hig/guidelines/keyboard.html) · [KDE accessibility](https://develop.kde.org/hig/accessibility/)
- Inspect accessible names, roles, values, disabled states and feedback with GTK Inspector and Orca. Test with the screen off; do not rely on color, sound or animation alone. [GTK accessibility](https://docs.gtk.org/gtk4/section-accessibility.html) · [GNOME accessibility](https://developer.gnome.org/hig/guidelines/accessibility.html)

## Result format

| Page/state | Environment and size | Keyboard / screen reader | Screenshot inspected | Result or issue |
| --- | --- | --- | --- | --- |
| _Example: Preferences / unavailable_ | _Desktop, GTK, backend, scale, size_ | _Pass, fail or not tested_ | _Filename or not captured_ | _Pass, fail or not tested; issue link_ |
