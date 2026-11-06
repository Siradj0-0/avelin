"""Dashboard view and sampling behavior."""
from collections import deque

from .. import system


class DashboardMixin:
    """Existing dashboard behavior, shared with the application window."""

    def _init_dashboard(self):
        self.prev_cpu = None
        self.cpu_history = deque(maxlen=60)
        self.mem_history = deque(maxlen=60)
        self.metric_labels = {}
        self.metric_descriptions = {}

    def dashboard(self):
        from ..app import Gtk, box, label, spacer
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
        values = {'cpu': cpu, 'memory': None if mem is None or mem[1] <= 0 else 100 * mem[0] / mem[1],
                  'disk': None if disk is None or disk[1] <= 0 else 100 * disk[0] / disk[1]}
        for key, value in values.items():
            self.metric_labels[key].set_text('—' if value is None else f'{value:.0f}%')
            description, base = self.metric_descriptions[key]
            description.set_text(base + (' · unavailable' if value is None else ''))
        self.cpu_history.append(cpu)
        self.mem_history.append(values['memory'])
        self.graph.queue_draw()
        return True

