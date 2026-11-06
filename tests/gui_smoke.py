"""Run under Xvfb with distribution GTK/PyGObject dependencies installed."""
from unittest.mock import patch
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gtk
from avelin.app import Window

app = Gtk.Application(application_id='io.github.siradj00.avelin.test')
errors = []

def activate(application):
    try:
        with patch.object(Window, 'check_update', lambda self: None):
            window = Window(application)
        window.present()
        for name in ('dashboard', 'tune', 'cleanup', 'system'):
            assert window.stack.get_child_by_name(name) is not None
        def finish():
            window.close()
            application.quit()
            return False
        GLib.timeout_add(500, finish)
    except Exception as exc:
        errors.append(str(exc))
        application.quit()

app.connect('activate', activate)
app.run([])
if errors:
    raise SystemExit('; '.join(errors))
