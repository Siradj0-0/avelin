"""GTK 4 interface. Privileged system modification is deliberately absent."""
from collections import deque
import shutil
import threading
import gi
gi.require_version('Gtk', '4.0')
gi.require_foreign('cairo')
from gi.repository import Gdk, Gio, GLib, Gtk
from . import __version__, actions, storage, system, updates

CSS = b'''
window { background: #17191c; color: #f2f2ef; }
.sidebar { background: #1d2024; border-right: 1px solid #353a40; padding: 26px 18px; }
.brand { font-size: 23px; font-weight: 700; }
.overline { color: #aebbb3; font-size: 12px; font-weight: 600; }
.nav { padding: 11px 14px; margin-top: 5px; border-radius: 8px; background: transparent; box-shadow: none; color: #c2c7c5; }
.nav:hover { background: #2b3030; color: #ffffff; }
.nav:checked { background: #343d37; color: #d7f5de; font-weight: 700; }
button:focus-visible, switch:focus-visible, dropdown:focus-visible {
    outline: 2px solid #a6d5ff; outline-offset: 2px;
}
.main { padding: 34px 40px 38px; }
.title { font-size: 30px; font-weight: 700; }
.subtitle, .muted { color: #aab2af; }
.subtitle { font-size: 14px; }
.section-title { font-size: 18px; font-weight: 700; }
.card { background: #22262a; border: 1px solid #343a3d; border-radius: 12px; padding: 20px; }
.metric-value { font-size: 29px; font-weight: 700; }
.accent { color: #b6e8c2; }
.cpu-key { color: #b6e8c2; }
.memory-key { color: #91b3db; }
button.action { background: #bedfc4; color: #17251a; font-weight: 700; border-radius: 8px; padding: 9px 14px; }
button.secondary { background: #343a3d; color: #edf1ee; border-radius: 8px; padding: 8px 14px; }
button.danger { background: #644039; color: #fff0e9; border-radius: 8px; padding: 8px 14px; }
button.action:hover { background: #d5efda; }
button.secondary:hover { background: #495250; }
button.danger:hover { background: #805247; }
button.action:disabled, button.secondary:disabled, button.danger:disabled {
    background: #303437; color: #aeb5b1; opacity: 1;
}
.separator { background: #353a3d; min-height: 1px; }
'''


def label(text='', css='', wrap=False):
    w = Gtk.Label(label=text, xalign=0, wrap=wrap)
    if css:
        w.add_css_class(css)
    return w


def box(vertical=True, spacing=0, css=None):
    w = Gtk.Box(orientation=Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL, spacing=spacing)
    if css:
        w.add_css_class(css)
    return w


def button(text, css, callback):
    b = Gtk.Button(label=text)
    b.add_css_class(css)
    b.connect('clicked', callback)
    return b


def spacer():
    w = Gtk.Box()
    w.set_hexpand(True)
    return w


def details_row(title, value):
    row = box(False, 16)
    t = label(title, 'muted')
    t.set_size_request(130, -1)
    row.append(t)
    v = label(value, wrap=True)
    v.set_hexpand(True)
    v.set_selectable(True)
    row.append(v)
    return row


class Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Avelin')
        self.set_default_size(1120, 740)
        self.set_size_request(780, 560)
        self.prev_cpu = None
        self.cpu_history = deque(maxlen=60)
        self.mem_history = deque(maxlen=60)
        self.metric_labels = {}
        self.metric_descriptions = {}
        self.update_label = None
        root = box(False)
        self.set_child(root)
        sidebar = box(True, 8, 'sidebar')
        sidebar.set_size_request(190, -1)
        root.append(sidebar)
        brand = box(False, 10)
        brand.append(label('avelin', 'brand'))
        sidebar.append(brand)
        intro = label('A clearer view of your system', 'overline', True)
        intro.set_margin_top(6)
        intro.set_margin_bottom(30)
        sidebar.append(intro)
        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        # Page changes do not depend on animation or a desktop motion setting.
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)
        first = None
        for key, name, builder in [('dashboard', 'Dashboard', self.dashboard), ('tune', 'Preferences', self.tune), ('cleanup', 'Clean up', self.cleanup), ('system', 'System', self.system_page)]:
            page = builder()
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scroll.set_child(page)
            self.stack.add_named(scroll, key)
            nav = Gtk.ToggleButton(label=name)
            nav.add_css_class('nav')
            nav.set_halign(Gtk.Align.FILL)
            if first:
                nav.set_group(first)
            else:
                first = nav
            nav.connect('toggled', self.select_page, key)
            sidebar.append(nav)
        first.set_active(True)
        side_bottom = Gtk.Box()
        side_bottom.set_vexpand(True)
        sidebar.append(side_bottom)
        sidebar.append(label('Made for Linux', 'overline'))
        sidebar.append(label('Open source  /  v' + __version__, 'muted'))
        root.append(self.stack)
        self.sample()
        GLib.timeout_add_seconds(2, self.sample)
        self.check_update()

    def select_page(self, toggle, key):
        if toggle.get_active():
            self.stack.set_visible_child_name(key)

    def page(self, overline, title, subtitle):
        p = box(True, 14, 'main')
        p.append(label(title, 'title'))
        sub = label(subtitle, 'subtitle', True)
        sub.set_margin_bottom(14)
        p.append(sub)
        return p

    def dashboard(self):
        p = self.page('Overview', 'Your system at a glance', 'Live measurements, with no automatic system changes.')
        row = box(False, 12)
        for key, name, description in [('cpu', 'Processor', 'CPU utilization'), ('memory', 'Memory', 'RAM in use'), ('disk', 'Storage', 'Root filesystem used')]:
            card = box(True, 9, 'card')
            card.set_hexpand(True)
            card.append(label(name, 'overline'))
            value = label('—', 'metric-value')
            self.metric_labels[key] = value
            card.append(value)
            description_label = label(description, 'muted', True)
            self.metric_descriptions[key] = (description_label, description)
            card.append(description_label)
            row.append(card)
        p.append(row)
        graph_card = box(True, 10, 'card')
        head = box(False, 8)
        head.append(label('Recent activity', 'section-title'))
        head.append(spacer())
        head.append(label('Solid: CPU', 'cpu-key'))
        head.append(label('Dashed: Memory', 'memory-key'))
        graph_card.append(head)
        graph_card.append(label('Last 2 minutes · sampled every 2 seconds · 0–100%', 'muted'))
        self.graph = Gtk.DrawingArea()
        self.graph.set_content_height(180)
        self.graph.set_hexpand(True)
        self.graph.set_draw_func(self.draw_graph)
        graph_card.append(self.graph)
        p.append(graph_card)
        note = label('GPU activity is not available yet. Storage shows capacity, not disk I/O.', 'muted', True)
        p.append(note)
        return p

    def draw_graph(self, area, cr, width, height):
        for y in (0, 0.5, 1):
            cr.set_source_rgba(1, 1, 1, 0.10)
            cr.set_line_width(1)
            cr.move_to(0, (height - 2) * y + 1)
            cr.line_to(width, (height - 2) * y + 1)
            cr.stroke()
        for values, color, dash in ((self.cpu_history, (0.70, 0.90, 0.75), ()), (self.mem_history, (0.57, 0.70, 0.86), (6, 4))):
            cr.set_dash(dash)
            cr.set_source_rgb(*color)
            cr.set_line_width(2)
            started = False
            for i, val in enumerate(values):
                if val is None:
                    started = False
                    continue
                x = width * (i + 60 - len(values)) / 59
                y = (height - 2) * (1 - min(100, max(0, val)) / 100) + 1
                if started:
                    cr.line_to(x, y)
                else:
                    cr.move_to(x, y)
                    started = True
            cr.stroke()

    def sample(self):
        now = system.cpu_ticks()
        cpu = system.cpu_percent(self.prev_cpu, now)
        self.prev_cpu = now
        mem, disk = system.memory(), system.disk()
        values = {'cpu': cpu, 'memory': None if mem is None else 100 * mem[0] / mem[1],
                  'disk': None if disk is None else 100 * disk[0] / disk[1]}
        for key, value in values.items():
            self.metric_labels[key].set_text('—' if value is None else f'{value:.0f}%')
            description, base = self.metric_descriptions[key]
            description.set_text(base + (' · unavailable' if value is None else ''))
        self.cpu_history.append(cpu)
        self.mem_history.append(None if mem is None else 100 * mem[0] / mem[1])
        self.graph.queue_draw()
        return True

    def tune(self):
        p = self.page('Adjustments', 'Preferences', 'Change a preference and switch it back whenever you like.')
        power = box(True, 10, 'card')
        power_label = label('Power profile', 'section-title')
        power.append(power_label)
        power.append(label('This system-wide profile affects the whole machine, not just your session. Performance mode may use more power, generate heat and reduce battery life.', 'muted', True))
        self.power_status = label('Checking power profiles…', 'muted', True)
        power.append(self.power_status)
        row = box(False, 8)
        self.power_choices = Gtk.DropDown.new_from_strings([])
        self.power_choices.set_hexpand(True)
        self.power_choices.set_tooltip_text('Choose a power profile to apply')
        self.power_choices.set_sensitive(False)
        self.power_apply = button('Apply…', 'secondary', self.confirm_power)
        self.power_apply.set_sensitive(False)
        power_label.set_mnemonic_widget(self.power_choices)
        row.append(self.power_choices)
        row.append(self.power_apply)
        power.append(row)
        p.append(power)
        self.power_ids = []
        self.refresh_power()
        self.tune_feedback = label('Desktop preferences apply to your current GNOME session.', 'muted', True)
        p.append(self.tune_feedback)
        group = None
        for item in actions.SETTINGS:
            if item.group != group:
                group = item.group
                heading = label(group, 'section-title')
                heading.set_margin_top(10)
                p.append(heading)
            row = box(False, 18, 'card')
            text = box(True, 6)
            text.set_hexpand(True)
            setting_label = label(item.title, 'section-title', True)
            text.append(setting_label)
            text.append(label(item.description, 'muted', True))
            row.append(text)
            switch = Gtk.Switch()
            setting_label.set_mnemonic_widget(switch)
            state = actions.setting_state(item.key)
            switch.set_valign(Gtk.Align.CENTER)
            switch.set_tooltip_text(item.title + ('' if state is not None else ' — unavailable in this session'))
            switch.set_sensitive(state is not None)
            if state is not None:
                switch.set_active(state)
                switch.connect('state-set', self.on_setting, item.key)
            else:
                text.append(label('Unavailable on this desktop', 'muted'))
            row.append(switch)
            p.append(row)
        p.append(label('These are desktop preferences, not a promise of better performance. More system options need testing and a recovery design.', 'muted', True))
        return p

    def refresh_power(self):
        self.power_choices.set_sensitive(False)
        self.power_apply.set_sensitive(False)
        self.power_status.set_text('Checking power profiles…')
        def work():
            profiles, current = actions.power_profiles()
            GLib.idle_add(self.show_power, profiles, current)
        threading.Thread(target=work, daemon=True).start()

    def show_power(self, profiles, current):
        self.power_ids = profiles
        names = {'power-saver': 'Power saver', 'balanced': 'Balanced', 'performance': 'Performance'}
        self.power_choices.set_model(Gtk.StringList.new([names[x] for x in profiles]))
        if current in profiles:
            self.power_choices.set_selected(profiles.index(current))
            self.power_status.set_text('Current profile: ' + names[current])
            self.power_choices.set_sensitive(True)
            self.power_apply.set_sensitive(True)
        else:
            self.power_status.set_text('Power profiles are unavailable on this system.')
        return False

    def confirm_power(self, _button):
        index = self.power_choices.get_selected()
        if index >= len(self.power_ids):
            return
        profile = self.power_ids[index]
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.NONE, text='Change power profile?')
        dialog.set_property('secondary-text', 'Apply ' + profile + ' system-wide? This affects the whole machine. Performance mode may increase heat and power use. You can select another available profile to reverse this change.')
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Apply', Gtk.ResponseType.ACCEPT)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        def response(d, result):
            d.destroy()
            if result != Gtk.ResponseType.ACCEPT:
                return
            self.power_apply.set_sensitive(False)
            self.power_status.set_text('Applying power profile…')
            def work():
                try:
                    actions.set_power_profile(profile)
                    GLib.idle_add(self.refresh_power)
                except Exception as exc:
                    GLib.idle_add(self.power_failed, str(exc))
            threading.Thread(target=work, daemon=True).start()
        dialog.connect('response', response)
        dialog.present()

    def power_failed(self, message):
        self.power_status.set_text('Could not change profile: ' + message)
        self.power_apply.set_sensitive(bool(self.power_ids))
        return False

    def on_setting(self, switch, desired, key):
        try:
            actions.set_setting(key, desired)
            self.tune_feedback.set_text('Preference updated. Toggle it again to change it back.')
            switch.set_state(desired)
        except Exception as exc:
            self.tune_feedback.set_text('Could not update the preference: ' + str(exc))
            switch.set_active(switch.get_state())
        return True

    def cleanup(self):
        p = self.page('Storage care', 'Find space, safely', 'Start with a read-only scan. Review your files before deleting anything.')
        card = box(True, 12, 'card')
        card.append(label('Where space goes', 'section-title'))
        card.append(label('Inspect common cache, trash, package and journal locations. Flatpak data can include installed apps and is not automatically disposable.', 'muted', True))
        row = box(False)
        self.scan_button = button('Scan storage', 'action', self.scan_storage)
        row.append(self.scan_button)
        row.append(spacer())
        card.append(row)
        self.scan_results = box(True, 10)
        self.scan_results.append(label('No scan run yet.', 'muted'))
        card.append(self.scan_results)
        card.append(label('Sizes estimate allocated regular-file space, not reclaimable space. Partial results are subtotals; access errors, shared data and scan limits can affect them.', 'muted', True))
        card.append(label('Entries on a different device are skipped. Same-device bind mounts may still be traversed, including outside the intended tree. Initial path prefixes may contain symbolic links.', 'muted', True))
        p.append(card)
        trash = box(True, 12, 'card')
        trash.append(label('Empty trash', 'section-title'))
        trash.append(label('Permanently removes trash from locations managed by your desktop, including supported mounted volumes. This cannot be undone. Check your trash first.', 'muted', True))
        row = box(False)
        self.trash_button = button('Empty trash…', 'danger', self.confirm_trash)
        trash_available = shutil.which('gio') is not None
        self.trash_button.set_sensitive(trash_available)
        row.append(self.trash_button)
        row.append(spacer())
        trash.append(row)
        self.cleanup_feedback = label('Nothing has been removed.' if trash_available else 'Empty trash is unavailable: gio is not installed.', 'muted', True)
        trash.append(self.cleanup_feedback)
        p.append(trash)
        p.append(label('No caches, logs, application data or packages are removed by the scan.', 'muted', True))
        return p

    def scan_storage(self, _button):
        self.scan_button.set_sensitive(False)
        while child := self.scan_results.get_first_child():
            self.scan_results.remove(child)
        self.scan_results.append(label('Scanning…', 'muted'))
        def work():
            try:
                results = storage.scan()
                GLib.idle_add(self.show_scan, results, None)
            except Exception as exc:
                GLib.idle_add(self.show_scan, [], str(exc))
        threading.Thread(target=work, daemon=True).start()

    def show_scan(self, results, error):
        while child := self.scan_results.get_first_child():
            self.scan_results.remove(child)
        if error:
            self.scan_results.append(label('Scan failed: ' + error, 'muted', True))
        if not error and not results:
            self.scan_results.append(label('Scan complete. No locations were reported.', 'muted', True))
        for result in results:
            line = box(True, 3)
            size = system.bytes_label(result.allocated_bytes)
            line.append(label(result.name + '  —  ' + result.status.capitalize() + '  ·  ' + size, 'section-title', True))
            line.append(label(result.path + '  ·  ' + result.note, 'muted', True))
            self.scan_results.append(line)
        self.scan_button.set_sensitive(True)
        return False

    def confirm_trash(self, _button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.NONE, text='Permanently empty trash?')
        dialog.set_property('secondary-text', 'Files in trash, including on supported mounted volumes, will be permanently deleted. This cannot be undone.')
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Empty trash', Gtk.ResponseType.ACCEPT)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        dialog.connect('response', self.on_trash_response)
        dialog.present()

    def on_trash_response(self, dialog, response):
        dialog.destroy()
        if response != Gtk.ResponseType.ACCEPT:
            return
        self.trash_button.set_sensitive(False)
        self.cleanup_feedback.set_text('Emptying trash…')
        def work():
            try:
                actions.empty_trash()
                result = 'Trash emptied. Some inaccessible items may remain.'
            except Exception as exc:
                result = 'Could not empty trash: ' + str(exc)
            GLib.idle_add(self.trash_finished, result)
        threading.Thread(target=work, daemon=True).start()

    def trash_finished(self, result):
        self.cleanup_feedback.set_text(result)
        self.trash_button.set_sensitive(True)
        return False

    def system_page(self):
        p = self.page('Device', 'Know your machine.', 'Detected locally. Some details depend on your hardware and installed utilities.')
        c = box(True, 14, 'card')
        mem = system.memory()
        disk = system.disk()
        for name, value in [('Distribution', system.os_name()), ('Desktop', system.desktop()), ('Processor', system.cpu_name()), ('Graphics', '\n'.join(system.graphics())), ('Memory', system.bytes_label(mem[1]) if mem else 'Unavailable'), ('Root storage', system.bytes_label(disk[1]) if disk else 'Unavailable'), ('zram swap', system.zram_status())]:
            c.append(details_row(name, value))
        p.append(c)
        update = box(True, 10, 'card')
        update.append(label('Updates', 'section-title'))
        self.update_label = label('Checking GitHub releases…', 'muted', True)
        update.append(self.update_label)
        row = box(False, 8)
        row.append(button('Check again', 'secondary', lambda _: self.check_update()))
        row.append(button('Open releases', 'secondary', lambda _: Gtk.show_uri(self, updates.RELEASES_URL, 0)))
        row.append(spacer())
        update.append(row)
        update.append(label('Updates are not installed automatically. Use your package manager or review a release manually.', 'muted', True))
        p.append(update)
        return p

    def check_update(self):
        self.update_label.set_text('Checking GitHub releases…')
        def work():
            status, message = updates.check_latest()
            GLib.idle_add(self.update_label.set_text, message)
            if status == 'new':
                GLib.idle_add(self.show_update, message)
        threading.Thread(target=work, daemon=True).start()

    def show_update(self, message):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.NONE, text=message)
        dialog.set_property('secondary-text', 'Review the release and installation instructions. Avelin does not install updates itself yet.')
        dialog.add_button('Later', Gtk.ResponseType.CANCEL)
        dialog.add_button('View release', Gtk.ResponseType.ACCEPT)
        dialog.connect('response', lambda d, response: (d.destroy(), Gtk.show_uri(self, updates.RELEASES_URL, 0) if response == Gtk.ResponseType.ACCEPT else None))
        dialog.present()


def main():
    app = Gtk.Application(application_id='io.github.siradj00.avelin', flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
    def activate(application):
        # The interface is deliberately dark; native controls should match its surfaces.
        Gtk.Settings.get_default().set_property('gtk-application-prefer-dark-theme', True)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Window(application).present()
    app.connect('activate', activate)
    app.run(None)
