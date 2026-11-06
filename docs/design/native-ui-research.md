# Native UI research

Avelin is a GTK 4 desktop utility, including for older or resource-constrained systems. These are design requirements and proposals, not claims that the current UI already satisfies them.

## Structure and adaptiveness

- Keep the main workflows in a single window with shallow, predictable navigation. Use a view switcher for a few peer views or a sidebar for more sections. [GNOME navigation](https://developer.gnome.org/hig/guidelines/navigation.html)
- Start with constrained windows and retain all functionality as the window narrows; aim to support at least 1024 × 600 desktop displays. Prefer reflow and compact navigation to requiring horizontal scrolling. Check 1366 × 768 and narrow tiled windows with large text as well. [GNOME adaptive design](https://developer.gnome.org/hig/guidelines/adaptive.html)
- Where available, evaluate libadwaita navigation split views, breakpoints and clamps. Use content-driven breakpoints and retain a working GTK-only path; check the actual installed libadwaita version rather than assuming newer APIs exist. [libadwaita adaptive layouts](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/adaptive-layouts.html)
- GNOME Disks illustrates a device-list and details structure; borrow clear selection and inspection, not device-specific controls or an unverified visual style. [GNOME disk partition documentation](https://help.gnome.org/gnome-help/disk-partitions.html)

## Settings, changes and feedback

- Separate application preferences from changes to system configuration. Make scope, effect and availability explicit; do not call every desktop preference a performance improvement.
- Give each change a truthful review of its target, effect and risk. Only call a preview a dry run if the backend actually supports one. Do not infer deletions or reclaimable space from a scan. When a previously reviewed plan can go stale, revalidate before applying and ask for confirmation if its material effects change.
- Prefer undo for genuinely reversible actions; otherwise explain the target and irreversible consequences, provide a specific affirmative action and a cancel path, and do not make the destructive action the Return-key default. Dialogs should be parented and appear in response to an intentional action. [GNOME dialogs](https://developer.gnome.org/hig/patterns/feedback/dialogs.html)
- Distinguish loading, empty, unavailable, partial, error and completed states in text. Explain why a disabled action is unavailable and provide a practical next step where one exists. Keep consequential failures accessible after any transient feedback. [GNOME placeholders](https://developer.gnome.org/hig/patterns/feedback/placeholders.html) · [KDE status changes](https://develop.kde.org/hig/status_changes/)

## Accessibility and visual review

- Use native controls with short, distinct accessible names, role and state. Label icon-only actions; do not convey status through color alone or place essential information only in hover tooltips. Keep focus visible and distinct from selection. [GTK accessibility](https://docs.gtk.org/gtk4/section-accessibility.html) · [KDE accessibility](https://develop.kde.org/hig/accessibility/)
- Test complete flows with a keyboard, a screen reader, large text and high contrast. Verify focus placement and return after dialogs, error messages, disabled controls and selected navigation. Respect system motion settings. [GNOME accessibility](https://developer.gnome.org/hig/guidelines/accessibility.html)
- Test screenshots of each relevant page and state under a real GTK headless backend at desktop and constrained sizes; inspect them rather than treating rendering as review. Record toolkit, display size, scale and results. Headless screenshots and automated tests do not replace Orca or real-desktop checks.
- Keep dark styling quiet and consistent, while testing interaction with high-contrast themes and text scaling. Use the existing logo; avoid decorative gradients or redundant icons. No visual review is claimed by this document.
