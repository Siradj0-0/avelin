"""Headless regression coverage for extracted dashboard behavior."""
import unittest
from unittest.mock import Mock, patch

from . import DashboardMixin


class DashboardExtractionTests(unittest.TestCase):
    def setUp(self):
        self.view = DashboardMixin()
        self.view._init_dashboard()
        self.view.metric_labels = {key: Mock() for key in ('cpu', 'memory', 'disk')}
        self.view.metric_descriptions = {
            key: (Mock(), text) for key, text in (
                ('cpu', 'CPU utilization'), ('memory', 'RAM in use'),
                ('disk', 'Root filesystem used'))}
        self.view.graph = Mock()

    @patch('avelin.dashboard.system.disk', return_value=(25, 100))
    @patch('avelin.dashboard.system.memory', return_value=(40, 100))
    @patch('avelin.dashboard.system.cpu_percent', side_effect=[None, 25.0])
    @patch('avelin.dashboard.system.cpu_ticks', side_effect=[(10, 20), (20, 40)])
    def test_sampling_preserves_warmup_and_updates(self, ticks, percent, memory, disk):
        self.assertTrue(self.view.sample())
        self.view.metric_labels['cpu'].set_text.assert_called_with('—')
        self.view.metric_descriptions['cpu'][0].set_text.assert_called_with('CPU utilization · unavailable')
        self.assertTrue(self.view.sample())
        percent.assert_called_with((10, 20), (20, 40))
        self.view.metric_labels['cpu'].set_text.assert_called_with('25%')
        self.view.metric_labels['memory'].set_text.assert_called_with('40%')
        self.view.metric_labels['disk'].set_text.assert_called_with('25%')
        self.assertEqual(list(self.view.cpu_history), [None, 25.0])
        self.assertEqual(list(self.view.mem_history), [40.0, 40.0])
        self.assertEqual(self.view.graph.queue_draw.call_count, 2)

    @patch('avelin.dashboard.system.disk', return_value=None)
    @patch('avelin.dashboard.system.memory', return_value=None)
    @patch('avelin.dashboard.system.cpu_percent', return_value=None)
    @patch('avelin.dashboard.system.cpu_ticks', return_value=None)
    def test_unavailable_values_stay_gaps_and_history_is_bounded(self, *_):
        for _ in range(61):
            self.view.sample()
        for key, widget in self.view.metric_labels.items():
            widget.set_text.assert_called_with('—')
            self.assertTrue(self.view.metric_descriptions[key][0].set_text.call_args.args[0].endswith(' · unavailable'))
        self.assertEqual(len(self.view.cpu_history), 60)
        self.assertEqual(len(self.view.mem_history), 60)
        self.assertTrue(all(value is None for value in self.view.mem_history))

    def test_graph_breaks_lines_at_gaps_and_keeps_patterns(self):
        self.view.cpu_history.extend([20, None, 40, 50])
        self.view.mem_history.extend([None, 80])
        canvas = Mock()
        self.view.draw_graph(None, canvas, 200, 100)
        self.assertEqual([call.args[0] for call in canvas.set_dash.call_args_list], [(), (6, 4)])
        # Grid contributes three line segments; only one segment joins CPU points.
        self.assertEqual(canvas.line_to.call_count, 4)
        # Grid has three moves, then two CPU segments and one memory point.
        self.assertEqual(canvas.move_to.call_count, 6)


if __name__ == '__main__':
    unittest.main()
