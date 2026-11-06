# Avelin interface direction

## Purpose and audience

A native Linux companion for people who want an understandable view of an aging or storage-constrained machine. It should prioritize clarity, safety, keyboard access and legibility over visual spectacle. It must not imply that every toggle improves performance, or that every cache is safe to erase.

## Design decisions

- **Quiet, not anonymous:** dark charcoal surfaces, soft mint for active states and a restrained blue for memory data. The simple wordmark carries the brand; content is not decorated with unnecessary symbols.
- **Information before decoration:** a persistent sidebar groups Dashboard, Preferences, Storage and System; the dashboard shows real CPU/RAM history and filesystem capacity. Labels describe actual quantities and unsupported measurements never become zeros.
- **Progressive disclosure:** scan first, explain scope and uncertainty, then give each irreversible action a separate confirmation. Do not blend personal files or useful application data into a fake “junk” total.
- **Plain language:** sentence-case labels, concrete verbs and short descriptions. Action labels say what will happen. Risk, availability and errors are visible in text, not only color.
- **Native interaction:** GTK controls, focus behavior, desktop accessibility and system text scaling. Avoid relying on color alone, and keep motion optional and subtle.
- **Honest status:** distinguish detected, unavailable and not yet implemented. A release notification opens release information; it never pretends an unverified update is installed.

## Review gates

Before calling the visual design finished: inspect all screens at multiple window sizes on real GNOME, KDE and Xfce desktops; test keyboard navigation, screen-reader labels, contrast and scaling; exercise empty, loading, unsupported and error states. This work is pending; no visual or accessibility QA is claimed in v0.1.0.

## Research used

- [Anthropic frontend-design skill](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md): avoid boilerplate, plan a distinctive visual system, use direct copy and critique the result.
- [Impeccable](https://github.com/pbakaus/impeccable): review with critique and audit; harden error and overflow states. It is a research reference, not installed in the app.
- [GNOME design principles](https://developer.gnome.org/hig/principles.html): keep tasks simple, disclose detail progressively and prevent mistakes.
- [GTK accessibility](https://docs.gtk.org/gtk4/section-accessibility.html): prefer native controls and test with assistive technology.

## GTK UI accessibility pass

The interface uses a deliberate dark palette, with native controls requested in dark mode to avoid a light-control/dark-surface mismatch. Keyboard focus is outlined, selected navigation has a weight as well as a color change, and pages no longer crossfade. Content can scroll horizontally when text scaling or a narrow window makes the layout wider than the viewport. Visible labels are associated with the power selector and each desktop preference switch. CPU and memory lines use solid and dashed patterns in addition to color; current values are also shown as text. Unavailable measurements, scan status and limits, empty scans, missing trash support and in-progress trash removal have explicit states. Power profile changes are identified as system-wide.

Automated GTK checks cover label associations, navigation, CSS parsing, line patterns and selected state transitions. They do not substitute for screen-reader, keyboard-only, contrast, scaling or real-desktop checks. The fixed dark palette and GTK theme interaction still need evaluation with high-contrast themes and on GNOME, KDE and Xfce. Graph history has no equivalent detailed text series; current values are the non-visual alternative, not a full accessible history.

- [GTK accessibility guidance](https://docs.gtk.org/gtk4/section-accessibility.html): associate labels with controls and verify the accessibility tree with assistive technology.
- [GTK CSS properties](https://docs.gtk.org/gtk4/css-properties.html): GTK styles native widgets rather than browser elements.

Validation for this pass: four initial page views were inspected under Xvfb at 1120×740 and 780×560 with the default virtual-display theme; this is not a complete state, scaling or desktop review. Run the dedicated checks with `xvfb-run -a python3 -m unittest tests.test_ui_accessibility -v` using Python 3.10+ with GTK 4, PyGObject and cairo. They skip if the GTK bindings or a display are unavailable; the existing CI GTK smoke job does not yet run this test module.
