"""GTK 4 interface. Privileged system modification is deliberately absent."""
from collections import deque
import shutil
import threading
import gi
gi.require_version('Gtk', '4.0')
gi.require_foreign('cairo')
from gi.repository import Gdk, Gio, GLib, Gtk
from . import __version__, actions, system, updates

CSS = b'''
window { background: #17191c; color: #f2f2ef; }
.sidebar { background: #1d2024; border-right: 1px solid #353a40; padding: 26px 18px; }
.brand { font-size: 23px; font-weight: 800; letter-spacing: -1px; }
.overline { color: #a9b5ae; font-size: 11px; font-weight: 700; letter-spacing: 1.3px; }
.nav { padding: 11px 14px; margin-top: 5px; border-radius: 8px; background: transparent; box-shadow: none; color: #c2c7c5; }
.nav:checked { background: #343d37; color: #d7f5de; }
.main { padding: 34px 40px 38px; }
.title { font-size: 31px; font-weight: 750; letter-spacing: -0.8px; }
.subtitle, .muted { color: #aab2af; }
.subtitle { font-size: 14px; }
.section-title { font-size: 18px; font-weight: 700; }
.card { background: #22262a; border: 1px solid #343a3d; border-radius: 12px; padding: 20px; }
.metric-value { font-size: 29px; font-weight: 700; letter-spacing: -0.6px; }
.accent { color: #b6e8c2; }
.cpu-key { color: #b6e8c2; }
.memory-key { color: #91b3db; }
button.action { background: #bedfc4; color: #17251a; font-weight: 700; border-radius: 8px; padding: 9px 14px; }
button.secondary { background: #343a3d; color: #edf1ee; border-radius: 8px; padding: 8px 14px; }
button.danger { background: #644039; color: #fff0e9; border-radius: 8px; padding: 8px 14px; }
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
        self.update_label = None
        root = box(False)
        self.set_child(root)
        sidebar = box(True, 8, 'sidebar')
        sidebar.set_size_request(190, -1)
        root.append(sidebar)
        brand = box(False, 10)
        icon = label('◈', 'accent')
        brand.append(icon)
        brand.append(label('avelin', 'brand'))
        sidebar.append(brand)
        intro = label('YOUR SYSTEM, CLEARER', 'overline')
        intro.set_margin_top(6)
        intro.set_margin_bottom(30)
        sidebar.append(intro)
        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        first = None
        for key, name, builder in [('dashboard', 'Dashboard', self.dashboard), ('tune', 'Tune', self.tune), ('cleanup', 'Clean up', self.cleanup), ('system', 'System', self.system_page)]:
            page = builder()
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
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
        sidebar.append(label('BUILT FOR LINUX', 'overline'))
        sidebar.append(label('Open source · v' + __version__, 'muted'))
        root.append(self.stack)
        self.sample()
        GLib.timeout_add_seconds(2, self.sample)
        self.check_update()

    def select_page(self, toggle, key):
        if toggle.get_active():
            self.stack.set_visible_child_name(key)

    def page(self, overline, title, subtitle):
        p = box(True, 14, 'main')
        p.append(label(overline.upper(), 'overline'))
        p.append(label(title, 'title'))
        sub = label(subtitle, 'subtitle', True)
        sub.set_margin_bottom(14)
        p.append(sub)
        return p

    def dashboard(self):
        p = self.page('Overview', 'A little more clarity.', 'A live look at the essentials. No system changes happen automatically.')
        row = box(False, 12)
        for key, name, description in [('cpu', 'PROCESSOR', 'CPU utilization'), ('memory', 'MEMORY', 'RAM in use'), ('disk', 'STORAGE', 'Root filesystem used')]:
            card = box(True, 9, 'card')
            card.set_hexpand(True)
            card.append(label(name, 'overline'))
            value = label('—', 'metric-value')
            self.metric_labels[key] = value
            card.append(value)
            card.append(label(description, 'muted'))
            row.append(card)
        p.append(row)
        graph_card = box(True, 10, 'card')
        head = box(False, 8)
        head.append(label('Recent activity', 'section-title'))
        head.append(spacer())
        head.append(label('● CPU', 'cpu-key'))
        head.append(label('● Memory', 'memory-key'))
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
        for values, color in ((self.cpu_history, (0.70, 0.90, 0.75)), (self.mem_history, (0.57, 0.70, 0.86))):
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
        self.metric_labels['cpu'].set_text('—' if cpu is None else f'{cpu:.0f}%')
        self.metric_labels['memory'].set_text('—' if mem is None else f'{100 * mem[0] / mem[1]:.0f}%')
        self.metric_labels['disk'].set_text('—' if disk is None else f'{100 * disk[0] / disk[1]:.0f}%')
        self.cpu_history.append(cpu)
        self.mem_history.append(None if mem is None else 100 * mem[0] / mem[1])
        self.graph.queue_draw()
        return True

    def tune(self):
        p = self.page('Adjustments', 'Make it yours.', 'Small changes, clearly explained. Only supported settings are shown.')
        card = box(True, 14, 'card')
        row = box(False, 18)
        text = box(True, 6)
        text.set_hexpand(True)
        text.append(label('Desktop animations', 'section-title'))
        text.append(label('Turn off GNOME animations to reduce visual effects. Change this back at any time.', 'muted', True))
        row.append(text)
        switch = Gtk.Switch()
        state = actions.animation_state()
        switch.set_valign(Gtk.Align.CENTER)
        switch.set_sensitive(state is not None)
        if state is not None:
            switch.set_active(state)
            switch.connect('state-set', self.on_animations)
        row.append(switch)
        card.append(row)
        self.tune_feedback = label('Available on GNOME only.' if state is None else 'Reads and changes your current GNOME preference.', 'muted', True)
        card.append(self.tune_feedback)
        p.append(card)
        p.append(label('More options, including zram and desktop changes, require design and safety testing before they can be enabled.', 'muted', True))
        return p

    def on_animations(self, switch, desired):
        try:
            actions.set_animations(desired)
            self.tune_feedback.set_text('Updated. Toggle again to restore the other value.')
            switch.set_state(desired)
        except Exception as exc:
            # Remain on the original state if the action failed.
            self.tune_feedback.set_text('Could not update animations: ' + str(exc))
            switch.set_active(switch.get_state())
        return True

    def cleanup(self):
        p = self.page('Storage care', 'Keep what matters.', 'Review each action before you remove anything. Cleanup is never automatic.')
        card = box(True, 14, 'card')
        card.append(label('Empty trash', 'section-title'))
        card.append(label('Permanently removes trashed files from locations managed by your desktop, including supported mounted volumes. This cannot be undone. Check your trash first.', 'muted', True))
        row = box(False)
        action = button('Empty trash…', 'danger', self.confirm_trash)
        action.set_sensitive(shutil.which('gio') is not None)
        row.append(action)
        row.append(spacer())
        card.append(row)
        self.cleanup_feedback = label('Nothing has been removed.', 'muted', True)
        card.append(self.cleanup_feedback)
        p.append(card)
        p.append(label('Package caches, old logs and application data are not deleted by this version.', 'muted', True))
        return p

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
        self.cleanup_feedback.set_text('Emptying trash…')
        def work():
            try:
                actions.empty_trash()
                result = 'Trash emptied. Some inaccessible items may remain.'
            except Exception as exc:
                result = 'Could not empty trash: ' + str(exc)
            GLib.idle_add(self.cleanup_feedback.set_text, result)
        threading.Thread(target=work, daemon=True).start()

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
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Window(application).present()
    app.connect('activate', activate)
    app.run(None)
