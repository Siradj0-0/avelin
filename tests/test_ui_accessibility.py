"""GTK UI behavior checks. Run with a display, e.g. xvfb-run -a python -m unittest tests.test_ui_accessibility."""
import unittest
from unittest.mock import Mock, patch

try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_foreign('cairo')
    from gi.repository import Gio, GLib, Gtk
    from avelin import actions, storage, system
    from avelin.app import CSS, Window
    GTK_AVAILABLE = Gtk.init_check()
except (ImportError, ValueError):
    GTK_AVAILABLE = False


def descendants(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from descendants(child)
        child = child.get_next_sibling()


@unittest.skipUnless(GTK_AVAILABLE, 'GTK 4, PyGObject, cairo and a display are required')
class UIAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Gtk.Application(application_id='io.github.siradj00.avelin.uitest',
                                  flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)

    def setUp(self):
        self.patches = [patch.object(Window, 'check_update'),
                        patch.object(Window, 'refresh_power'),
                        patch.object(actions, 'setting_state', return_value=None),
                        patch.object(GLib, 'timeout_add_seconds', return_value=0)]
        for item in self.patches:
            item.start()
        self.window = Window(self.app)

    def tearDown(self):
        self.window.destroy()
        for item in reversed(self.patches):
            item.stop()

    def test_stylesheet_parses(self):
        provider = Gtk.CssProvider()
        errors = []
        provider.connect('parsing-error', lambda _p, _section, error: errors.append(str(error)))
        provider.load_from_data(CSS)
        self.assertEqual(errors, [])

    def test_navigation_and_scroll_policy(self):
        for widget in descendants(self.window):
            if isinstance(widget, Gtk.ToggleButton) and widget.get_label() == 'Clean up':
                widget.set_active(True)
                break
        else:
            self.fail('Clean up navigation not found')
        self.assertEqual(self.window.stack.get_visible_child_name(), 'cleanup')
        scroll = self.window.stack.get_child_by_name('cleanup')
        self.assertEqual(scroll.get_policy()[0], Gtk.PolicyType.AUTOMATIC)
        self.assertEqual(self.window.stack.get_transition_type(), Gtk.StackTransitionType.NONE)

    def test_controls_have_visible_associated_labels(self):
        labels = [widget for widget in descendants(self.window) if isinstance(widget, Gtk.Label)]
        associations = {widget.get_text(): widget.get_mnemonic_widget() for widget in labels
                        if widget.get_mnemonic_widget() is not None}
        self.assertIs(associations['Power profile'], self.window.power_choices)
        for item in actions.SETTINGS:
            self.assertIsInstance(associations[item.title], Gtk.Switch)
            self.assertFalse(associations[item.title].get_sensitive())

    def test_missing_metrics_and_scan_states_are_explicit(self):
        with patch.object(system, 'cpu_ticks', return_value=None), \
             patch.object(system, 'cpu_percent', return_value=None), \
             patch.object(system, 'memory', return_value=None), \
             patch.object(system, 'disk', return_value=None):
            self.window.sample()
        for key in ('cpu', 'memory', 'disk'):
            self.assertEqual(self.window.metric_labels[key].get_text(), '—')
            self.assertIn('unavailable', self.window.metric_descriptions[key][0].get_text())
        self.window.show_scan([], None)
        self.assertIn('No locations', self.window.scan_results.get_first_child().get_text())
        self.window.show_scan([], 'permission denied')
        self.assertIn('Scan failed: permission denied', self.window.scan_results.get_first_child().get_text())
        self.assertTrue(self.window.scan_button.get_sensitive())

    def test_scope_and_scan_status_are_explicit(self):
        texts = [widget.get_text() for widget in descendants(self.window)
                 if isinstance(widget, Gtk.Label)]
        self.assertTrue(any('system-wide' in text and 'whole machine' in text for text in texts))
        self.assertTrue(any('different device' in text and 'bind mounts' in text
                            and 'path prefixes' in text for text in texts))
        result = storage.AuditResult('Cache', '/example', 512, 'partial', 'Partial subtotal: entry limit')
        self.window.show_scan([result], None)
        labels = [widget.get_text() for widget in descendants(self.window.scan_results)
                  if isinstance(widget, Gtk.Label)]
        self.assertTrue(any('Partial' in text and '512 B' in text for text in labels))
        self.assertTrue(any('entry limit' in text for text in labels))

    def test_trash_action_disabled_until_completion(self):
        dialog = Mock()
        with patch('avelin.app.threading.Thread') as thread:
            self.window.on_trash_response(dialog, Gtk.ResponseType.ACCEPT)
            dialog.destroy.assert_called_once()
            self.assertFalse(self.window.trash_button.get_sensitive())
            self.assertEqual(self.window.cleanup_feedback.get_text(), 'Emptying trash…')
            thread.return_value.start.assert_called_once()
        self.window.trash_finished('Could not empty trash: denied')
        self.assertTrue(self.window.trash_button.get_sensitive())
        self.assertIn('denied', self.window.cleanup_feedback.get_text())

    def test_graph_uses_distinct_line_patterns(self):
        cr = Mock()
        self.window.draw_graph(None, cr, 200, 100)
        self.assertEqual([call.args[0] for call in cr.set_dash.call_args_list], [(), (6, 4)])
