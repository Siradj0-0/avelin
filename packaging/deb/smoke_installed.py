"""Smoke-test the installed GTK window, without importing a checkout."""
import sys
from unittest.mock import patch

sys.path.insert(0, '/usr/lib/avelin')
import avelin
assert avelin.__file__ == '/usr/lib/avelin/avelin/__init__.py', avelin.__file__
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gtk
from avelin.app import Window

app = Gtk.Application(application_id='io.github.siradj00.avelin.packagingtest')
errors = []
def activate(application):
    try:
        with patch.object(Window, 'check_update', lambda self: None):
            window = Window(application)
        window.present()
        for name in ('dashboard', 'tune', 'cleanup', 'system'):
            assert window.stack.get_child_by_name(name) is not None, name
        def finish():
            window.close()
            application.quit()
            return False
        GLib.timeout_add(500, finish)
    except Exception as exc:
        errors.append(repr(exc))
        application.quit()
app.connect('activate', activate)
app.run([])
if errors:
    raise SystemExit('; '.join(errors))
