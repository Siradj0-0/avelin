"""GTK UI behavior checks. Run with a display, e.g. xvfb-run -a python -m unittest tests.test_ui_accessibility."""
import os
import unittest
from unittest.mock import Mock, patch

try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Gdk', '4.0')
    gi.require_foreign('cairo')
    from gi.repository import Gdk, Gio, GLib, Gtk
    from avelin import actions, storage, system
    from avelin.app import CSS, Window
    Gtk.init_check()
    GTK_AVAILABLE = Gdk.Display.get_default() is not None
except (ImportError, ValueError):
    GTK_AVAILABLE = False

if os.environ.get('AVELIN_REQUIRE_GTK') == '1' and not GTK_AVAILABLE:
    raise RuntimeError('GTK 4, PyGObject, cairo and a display are required for UI tests')


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
        self.assertTrue(any('system-wide' in text and 'temporarily unavailable' in text
                            and 'will not restore those holds' in text for text in texts))
        self.assertTrue(any('different device' in text and 'bind mounts' in text
                            and 'path prefixes' in text for text in texts))
        result = storage.AuditResult('Cache', '/example', 512, 'partial', 'Partial subtotal: entry limit')
        self.window.show_scan([result], None)
        labels = [widget.get_text() for widget in descendants(self.window.scan_results)
                  if isinstance(widget, Gtk.Label)]
        self.assertTrue(any('Partial' in text and '512 B' in text for text in labels))
        self.assertTrue(any('entry limit' in text for text in labels))

    def test_power_changes_are_unavailable_and_fail_closed(self):
        self.window.show_power(['balanced', 'performance'], 'balanced')
        self.assertIn('Current profile: Balanced', self.window.power_status.get_text())
        self.assertIn('Changes temporarily unavailable', self.window.power_status.get_text())
        self.assertFalse(self.window.power_choices.get_sensitive())
        self.assertFalse(self.window.power_apply.get_sensitive())
        with patch('avelin.app.Gtk.MessageDialog') as dialog_type:
            self.window.confirm_power(None)
            dialog_type.assert_not_called()
        self.window.power_failed('Blocked to protect active holds')
        self.assertIn('Blocked to protect active holds', self.window.power_status.get_text())
        self.assertIn('temporarily unavailable', self.window.power_status.get_text())
        self.assertFalse(self.window.power_choices.get_sensitive())
        self.assertFalse(self.window.power_apply.get_sensitive())

    def test_power_confirmation_warns_about_holds(self):
        self.window.show_power(['balanced'], 'balanced')
        # The dialog remains protective if profile changes are deliberately re-enabled later.
        self.window.power_apply.set_sensitive(True)
        with patch('avelin.app.Gtk.MessageDialog') as dialog_type:
            self.window.confirm_power(None)
        dialog = dialog_type.return_value
        dialog.set_property.assert_called_once()
        name, warning = dialog.set_property.call_args.args
        self.assertEqual(name, 'secondary-text')
        self.assertIn('system-wide', warning)
        self.assertIn('cancel active power-profile holds', warning)
        self.assertIn('will not restore those holds', warning)
        dialog.set_default_response.assert_called_once_with(Gtk.ResponseType.CANCEL)
        dialog.present.assert_called_once()

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

    def test_setting_failure_reads_back_without_a_second_write(self):
        # The switch is attached to the window so the deferred callback can
        # distinguish live controls from widgets removed during shutdown.
        for initial, actual in ((False, False), (False, True), (True, True), (True, False), (False, None)):
            with self.subTest(initial=initial, actual=actual):
                switch = Gtk.Switch()
                switch.set_active(initial)
                self.window.get_child().get_first_child().append(switch)
                handler = switch.connect('state-set', self.window.on_setting, 'enable-animations')
                self.window.setting_handlers[switch] = handler
                with patch.object(actions, 'set_setting', side_effect=RuntimeError('write denied')) as write, \
                     patch.object(actions, 'setting_state', return_value=actual) as read:
                    switch.set_active(not initial)
                    self.assertFalse(switch.get_sensitive())
                    self.assertIn(switch, self.window.setting_pending)
                    while switch in self.window.setting_pending:
                        GLib.MainContext.default().iteration(False)
                write.assert_called_once_with('enable-animations', not initial)
                read.assert_called_once_with('enable-animations')
                expected = initial if actual is None else actual
                self.assertEqual(switch.get_active(), expected)
                self.assertEqual(switch.get_state(), expected)
                self.assertEqual(switch.get_sensitive(), actual is not None)
                self.assertIn('write denied', self.window.tune_feedback.get_text())
                self.assertNotIn('Preference updated', self.window.tune_feedback.get_text())
                if actual is None:
                    self.assertIn('Current state is unavailable', self.window.tune_feedback.get_text())
                switch.unparent()

    def test_setting_failure_handles_readback_error_and_removed_widget(self):
        switch = Gtk.Switch()
        self.window.get_child().get_first_child().append(switch)
        self.window.setting_handlers[switch] = switch.connect('state-set', self.window.on_setting, 'enable-animations')
        with patch.object(actions, 'set_setting', side_effect=RuntimeError('write denied')) as write, \
             patch.object(actions, 'setting_state', side_effect=RuntimeError('read failed')):
            switch.set_active(True)
            while switch in self.window.setting_pending:
                GLib.MainContext.default().iteration(False)
        write.assert_called_once()
        self.assertFalse(switch.get_sensitive())
        self.assertIn('write denied', self.window.tune_feedback.get_text())
        self.assertIn('Current state is unavailable', self.window.tune_feedback.get_text())
        switch.unparent()

        removed = Gtk.Switch()
        parent = self.window.get_child().get_first_child()
        parent.append(removed)
        self.window.setting_handlers[removed] = removed.connect('state-set', self.window.on_setting, 'enable-animations')
        with patch.object(actions, 'set_setting', side_effect=RuntimeError('write denied')) as write, \
             patch.object(actions, 'setting_state') as read:
            removed.set_active(True)
            parent.remove(removed)
            while removed in self.window.setting_pending:
                GLib.MainContext.default().iteration(False)
        write.assert_called_once()
        read.assert_not_called()

    def test_pending_guard_and_handler_unblocked_after_restore_error(self):
        switch = Gtk.Switch()
        self.window.get_child().get_first_child().append(switch)
        self.window.setting_handlers[switch] = switch.connect('state-set', self.window.on_setting, 'enable-animations')
        with patch.object(actions, 'set_setting', side_effect=RuntimeError('write denied')) as write, \
             patch.object(actions, 'setting_state', return_value=False), \
             patch.object(switch, 'set_state', side_effect=RuntimeError('restore failed')):
            switch.set_active(True)
            # A programmatic state-set during pending rollback must not write again.
            switch.set_active(False)
            while switch in self.window.setting_pending:
                GLib.MainContext.default().iteration(False)
        write.assert_called_once()
        self.assertFalse(switch.get_sensitive())
        self.assertIn('write denied', self.window.tune_feedback.get_text())
        self.assertIn('Current state is unavailable', self.window.tune_feedback.get_text())
        # Finally must unblock the handler even if restoring the widget fails.
        with patch.object(actions, 'set_setting') as write:
            switch.set_active(True)
            write.assert_called_once_with('enable-animations', True)
        switch.unparent()

    def test_zero_total_metrics_are_unavailable(self):
        with patch.object(system, 'cpu_ticks', return_value=None), \
             patch.object(system, 'cpu_percent', return_value=None), \
             patch.object(system, 'memory', return_value=(0, 0)), \
             patch.object(system, 'disk', return_value=(0, 0)):
            self.window.sample()
        for key in ('memory', 'disk'):
            self.assertEqual(self.window.metric_labels[key].get_text(), '—')
            self.assertIn('unavailable', self.window.metric_descriptions[key][0].get_text())
        self.assertIsNone(self.window.mem_history[-1])

    def test_trash_completion_does_not_claim_verified_deletion(self):
        with patch('avelin.app.threading.Thread') as thread, \
             patch.object(actions, 'empty_trash') as empty, \
             patch.object(GLib, 'idle_add', side_effect=lambda fn, arg: fn(arg)):
            self.window.on_trash_response(Mock(), Gtk.ResponseType.ACCEPT)
            thread.call_args.kwargs['target']()
        empty.assert_called_once()
        feedback = self.window.cleanup_feedback.get_text()
        self.assertIn('Verify your trash', feedback)
        self.assertIn('some items may remain', feedback)
        self.assertNotIn('Trash emptied', feedback)

    def test_graph_uses_distinct_line_patterns(self):
        cr = Mock()
        self.window.draw_graph(None, cr, 200, 100)
        self.assertEqual([call.args[0] for call in cr.set_dash.call_args_list], [(), (6, 4)])
