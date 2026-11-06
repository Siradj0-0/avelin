"""Combined UI/backend safety tests; subprocesses and workers are simulated."""
import os
import subprocess
import unittest
from unittest.mock import Mock, patch

try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Gdk', '4.0')
    gi.require_foreign('cairo')
    from gi.repository import Gdk, Gio, GLib, Gtk
    from avelin import actions
    from avelin.app import Window
    Gtk.init_check()
    GTK_AVAILABLE = Gdk.Display.get_default() is not None
except (ImportError, ValueError):
    GTK_AVAILABLE = False

if os.environ.get('AVELIN_REQUIRE_GTK') == '1' and not GTK_AVAILABLE:
    raise RuntimeError('GTK 4, PyGObject, cairo and a display are required')


class InlineThread:
    def __init__(self, target, daemon):
        self.target = target
    def start(self):
        self.target()


@unittest.skipUnless(GTK_AVAILABLE, 'GTK 4, PyGObject, cairo and a display are required')
class SafetyIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Gtk.Application(application_id='io.github.siradj00.avelin.safetytest',
                                  flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)

    def setUp(self):
        self.patches = [patch.object(Window, 'check_update'),
                        patch.object(Window, 'refresh_power'),
                        patch.object(actions, 'setting_state', return_value=None),
                        patch.object(GLib, 'timeout_add_seconds', return_value=0),
                        patch('avelin.app.threading.Thread', InlineThread),
                        patch.object(GLib, 'idle_add', side_effect=lambda fn, *args: fn(*args))]
        for item in self.patches:
            item.start()
        self.window = Window(self.app)

    def tearDown(self):
        self.window.destroy()
        for item in reversed(self.patches):
            item.stop()

    def test_power_controls_disabled_and_backend_blocks_forced_confirmation(self):
        self.window.show_power(['balanced', 'performance'], 'balanced')
        self.assertFalse(self.window.power_choices.get_sensitive())
        self.assertFalse(self.window.power_apply.get_sensitive())
        self.window.power_choices.set_selected(1)
        self.window.power_apply.set_sensitive(True)  # Defense in depth, not a normal user path.
        def read(command, **kwargs):
            self.assertIn(command, [['powerprofilesctl', 'list'], ['powerprofilesctl', 'get']])
            output = '* balanced:\n  performance:\n' if command[-1] == 'list' else 'balanced\n'
            return subprocess.CompletedProcess(command, 0, stdout=output)
        with patch('avelin.app.Gtk.MessageDialog') as dialog_type, \
             patch.object(actions.shutil, 'which', return_value='/usr/bin/powerprofilesctl'), \
             patch.object(actions.subprocess, 'run', side_effect=read) as run:
            self.window.confirm_power(None)
            dialog = dialog_type.return_value
            callback = dialog.connect.call_args.args[1]
            callback(dialog, Gtk.ResponseType.ACCEPT)
        self.assertEqual([c.args[0] for c in run.call_args_list],
                         [['powerprofilesctl', 'list'], ['powerprofilesctl', 'get']])
        self.assertIn('cannot restore', self.window.power_status.get_text())
        self.assertFalse(self.window.power_choices.get_sensitive())
        self.assertFalse(self.window.power_apply.get_sensitive())

    def test_trash_failure_reaches_ui_with_partial_deletion_warning(self):
        for failure in (subprocess.TimeoutExpired(['gio'], 180),
                        subprocess.CalledProcessError(1, ['gio'])):
            with self.subTest(failure=type(failure).__name__), \
                 patch.object(actions.shutil, 'which', return_value='/usr/bin/gio'), \
                 patch.object(actions.subprocess, 'run', side_effect=failure) as run:
                self.window.on_trash_response(Mock(), Gtk.ResponseType.ACCEPT)
                run.assert_called_once()
                self.assertIn('may already have been permanently deleted',
                              self.window.cleanup_feedback.get_text())
                self.assertTrue(self.window.trash_button.get_sensitive())

    def test_trash_cancel_and_success_messages(self):
        with patch.object(actions.subprocess, 'run') as run:
            self.window.on_trash_response(Mock(), Gtk.ResponseType.CANCEL)
            run.assert_not_called()
        with patch.object(actions.shutil, 'which', return_value='/usr/bin/gio'), \
             patch.object(actions.subprocess, 'run') as run:
            self.window.on_trash_response(Mock(), Gtk.ResponseType.ACCEPT)
            run.assert_called_once()
        self.assertIn('Verify your trash', self.window.cleanup_feedback.get_text())
        self.assertNotIn('Trash emptied', self.window.cleanup_feedback.get_text())


if __name__ == '__main__':
    unittest.main()
