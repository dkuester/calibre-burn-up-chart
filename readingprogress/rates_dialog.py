"""
Dialog for the purchase-rate vs. reading-rate chart.

Shows how many books were added and read per month as 12-month
averages, with the area between them shaded by whether the backlog
shrinks or grows. The raw monthly counts appear in the tooltip.
"""

from calibre_plugins.readingprogress.chart_common import (
    TIME_RANGES,
    compute_y_axis,
    fit_x_range,
    is_dark_background,
)
from calibre_plugins.readingprogress.chart_dialog import (
    ALIGN_CENTER,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    PEN_NOPEN,
    PEN_SOLID,
    RENDER_ANTIALIASING,
    RENDER_TEXT_ANTIALIASING,
    TOOLTIP_RADIUS,
    AxesRenderer,
    LegendRenderer,
    PlotScale,
    SeriesRenderer,
    _cursor_pos,
    _global_pos,
    add_export_buttons,
    add_time_range_box,
    build_series_colors,
    chrome_for,
    show_paint_error,
)
from calibre_plugins.readingprogress.localization import _
from qt.core import (
    QColor,
    QDialog,
    QFont,
    QHBoxLayout,
    QPainter,
    QPen,
    QPointF,
    QPolygonF,
    QPushButton,
    QRectF,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

# Room for title and key-figures line above the plot
MARGIN_TOP = 95

# Alpha of the shaded area between the averages
FILL_ALPHA = 55

# Months summed up in the key-figures line
SUMMARY_MONTHS = 12

# Headroom above the highest average, so the legend in the top right
# corner does not hide a peak
Y_HEADROOM = 1.25


def _with_alpha(color, alpha):
    faded = QColor(color)
    faded.setAlpha(alpha)
    return faded


class RatesChartWidget(QWidget):
    """Draws books added vs. books read per month.

    ``rates`` is the list from ``compute_rates()``:
    ``(date, added, read, added_avg, read_avg)`` per month.
    """

    def __init__(self, rates, decimal_sep='.', parent=None, colors=None,
                 time_range='all'):
        super().__init__(parent)
        self.rates = rates
        self.decimal_sep = decimal_sep
        self.time_range = time_range
        self.chrome = chrome_for(self)
        bg = self.chrome['background']
        series = build_series_colors(
            is_dark_background((bg.red(), bg.green(), bg.blue())), colors)
        self.color_added = series['backlog']
        self.color_read = series['read']
        self._axes = AxesRenderer()
        self._series = SeriesRenderer()
        self._legend = LegendRenderer()
        self.setMinimumSize(700, 450)
        self.setMouseTracking(True)

    def set_time_range(self, time_range):
        self.time_range = time_range
        self.update()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        try:
            self._do_paint()
        except Exception as e:
            show_paint_error(self, e)

    def _plot_rect(self):
        return QRectF(
            MARGIN_LEFT,
            MARGIN_TOP,
            max(50, self.width()  - MARGIN_LEFT - MARGIN_RIGHT),
            max(50, self.height() - MARGIN_TOP  - MARGIN_BOTTOM),
        )

    def _x_range(self):
        first, last = self.rates[0][0], self.rates[-1][0]
        return fit_x_range(first, last, last, self.time_range)

    def _scale(self, plot):
        """``(PlotScale, x_max, y_step)`` for the current time range, or
        None if the range is degenerate."""
        x_min, x_max = self._x_range()
        x_days = (x_max - x_min).days
        if x_days <= 0:
            return None
        visible = [r for r in self.rates if x_min <= r[0] <= x_max] \
            or self.rates
        y_step, y_max = compute_y_axis(
            Y_HEADROOM * max(max(r[3], r[4]) for r in visible), integer=True)
        return PlotScale(plot, x_min, x_days, y_max), x_max, y_step

    def _do_paint(self):
        painter = QPainter(self)
        painter.setRenderHint(RENDER_ANTIALIASING, True)
        painter.setRenderHint(RENDER_TEXT_ANTIALIASING, True)
        painter.fillRect(self.rect(), self.chrome['background'])

        if len(self.rates) < 2:
            painter.setPen(self.chrome['text'])
            painter.drawText(self.rect(), ALIGN_CENTER, _("No data"))
            painter.end()
            return

        plot = self._plot_rect()
        fit = self._scale(plot)
        if fit is None:
            painter.end()
            return
        scale, x_max, y_step = fit

        self._draw_header(painter, plot)
        self._axes.draw(painter, scale, x_max, scale.y_max, y_step,
                        self.chrome, y_title=_("Books per month"))

        painter.save()
        painter.setClipRect(plot)
        self._draw_balance(painter, scale)
        self._series.draw_series(painter, scale, self.rates, index=3,
                                 color=self.color_added, width=2.5)
        self._series.draw_series(painter, scale, self.rates, index=4,
                                 color=self.color_read, width=2.5)
        painter.restore()

        self._legend.draw_entries(painter, plot, [
            (_("Added (12-month average)"), self.color_added, PEN_SOLID),
            (_("Read (12-month average)"), self.color_read, PEN_SOLID),
            (_("TBR shrinking (more read than added)"),
             _with_alpha(self.color_read, FILL_ALPHA), None),
            (_("TBR growing (more added than read)"),
             _with_alpha(self.color_added, FILL_ALPHA), None),
        ], self.chrome)

        painter.end()

    def _draw_header(self, painter, plot):
        years = dict(TIME_RANGES).get(self.time_range)
        if years is None:
            title = _("Books added vs. read per month")
        else:
            title = _("Books added vs. read per month, last {years} "
                      "years").format(years=years)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(self.chrome['text'])
        painter.drawText(QRectF(plot.left(), 15, plot.width(), 30),
                         ALIGN_CENTER, title)

        recent = self.rates[-SUMMARY_MONTHS:]
        added = sum(r[1] for r in recent)
        read = sum(r[2] for r in recent)
        text = _("Last 12 months: {added} added · {read} read · "
                 "TBR {change}").format(added=added, read=read,
                                        change='{:+d}'.format(added - read))
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)
        painter.setPen(self.chrome['muted'])
        painter.drawText(QRectF(plot.left(), 50, plot.width(), 22),
                         ALIGN_CENTER, text)

    def _draw_balance(self, painter, scale):
        """Shades the area between the two averages: read color where
        more is read than added, added color where it is the other way
        round. Segments that cross are split at the crossing."""
        shrink = _with_alpha(self.color_read, FILL_ALPHA)
        grow = _with_alpha(self.color_added, FILL_ALPHA)
        painter.setPen(QPen(PEN_NOPEN))

        def point(row, index):
            return QPointF(scale.date_to_x(row[0]),
                           scale.value_to_y(row[index]))

        for a, b in zip(self.rates, self.rates[1:]):
            d_a = a[4] - a[3]
            d_b = b[4] - b[3]
            pa_add, pa_read = point(a, 3), point(a, 4)
            pb_add, pb_read = point(b, 3), point(b, 4)
            if d_a * d_b >= 0:
                painter.setBrush(shrink if d_a + d_b > 0 else grow)
                painter.drawPolygon(QPolygonF(
                    [pa_add, pb_add, pb_read, pa_read]))
                continue
            t = d_a / (d_a - d_b)
            cross = QPointF(pa_add.x() + t * (pb_add.x() - pa_add.x()),
                            pa_add.y() + t * (pb_add.y() - pa_add.y()))
            painter.setBrush(shrink if d_a > 0 else grow)
            painter.drawPolygon(QPolygonF([pa_add, cross, pa_read]))
            painter.setBrush(shrink if d_b > 0 else grow)
            painter.drawPolygon(QPolygonF([cross, pb_add, pb_read]))

    # ------------------------------------------------------------------
    # Tooltips
    # ------------------------------------------------------------------
    def _number(self, value):
        return '{:.1f}'.format(value).replace('.', self.decimal_sep)

    def mouseMoveEvent(self, event):
        if len(self.rates) < 2:
            return
        pos = _cursor_pos(event)
        plot = self._plot_rect()
        fit = self._scale(plot)
        if fit is None or not plot.contains(pos):
            QToolTip.hideText()
            return
        scale = fit[0]

        best = None
        best_dist = TOOLTIP_RADIUS
        for row in self.rates:
            dist = abs(scale.date_to_x(row[0]) - pos.x())
            if dist < best_dist:
                best_dist = dist
                best = row
        if best is None:
            QToolTip.hideText()
            return

        text = _("{month}\nAdded: {added} (average {added_avg})\n"
                 "Read: {read} (average {read_avg})").format(
            month=best[0].strftime('%m/%Y'),
            added=best[1], added_avg=self._number(best[3]),
            read=best[2], read_avg=self._number(best[4]))
        QToolTip.showText(_global_pos(event), text, self)


class RatesChartDialog(QDialog):
    """Dialog with the rates chart, time range, export buttons and Close."""

    def __init__(self, rates, decimal_sep='.', parent=None, colors=None,
                 time_range='all', on_time_range_changed=None):
        super().__init__(parent)
        self.setWindowTitle(_("Purchase rate vs. reading rate"))
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        self.chart = RatesChartWidget(rates, decimal_sep, self,
                                      colors=colors, time_range=time_range)
        layout.addWidget(self.chart, 1)

        row = QHBoxLayout()
        add_time_range_box(self, row, self.chart, time_range,
                           on_time_range_changed)
        add_export_buttons(row, self.chart, 'rates')
        row.addStretch()
        btn = QPushButton(_("Close"))
        btn.clicked.connect(self.reject)
        row.addWidget(btn)
        layout.addLayout(row)
