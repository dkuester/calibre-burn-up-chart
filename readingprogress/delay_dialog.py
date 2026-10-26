"""
Dialog for the reading-delay analysis.

Shows a scatter plot: x-axis = when it was read, y-axis = how long the
book sat unread on the shelf. Horizontal lines mark the median and mean
of the selected time range. Hovering a point names the book, clicking it
shows the book in calibre; the wheel zooms, dragging pans.
"""

from datetime import timedelta

from calibre_plugins.readingprogress.chart_common import (
    TIME_RANGES,
    View,
    compute_y_axis,
    delay_colors,
    delay_unit,
    fit_x_range,
    is_dark_background,
    nice_step,
    pan_view,
    year_tick_step,
    zoom_view,
)
from calibre_plugins.readingprogress.chart_dialog import (
    ALIGN_CENTER,
    ALIGN_RIGHT,
    ALIGN_VCENTER,
    CAP_ROUND,
    PEN_DASH,
    PEN_DOT,
    RENDER_ANTIALIASING,
    RENDER_TEXT_ANTIALIASING,
    TOOLTIP_RADIUS,
    ZOOM_IN_FACTOR,
    ZOOM_OUT_FACTOR,
    PlotScale,
    _cursor_pos,
    _global_pos,
    add_export_buttons,
    add_time_range_box,
    build_series_colors,
    chrome_for,
    show_paint_error,
)
from calibre_plugins.readingprogress.export_reading_status import (
    delay_statistics,
)
from calibre_plugins.readingprogress.localization import _
from qt.core import (
    QColor,
    QDialog,
    QFont,
    QFontMetrics,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPen,
    QPointF,
    QPushButton,
    QRectF,
    Qt,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

# Plot area margins (in pixels)
MARGIN_LEFT   = 95
MARGIN_RIGHT  = 30
MARGIN_TOP    = 95
MARGIN_BOTTOM = 65

# Empty space left and right of the points, as a share of the range
X_MARGIN_SHARE = 0.02

# A press that moves less than this (pixels) is a click, not a drag
CLICK_SLOP = 4.0

POINT_RADIUS = 3.5


class DelayChartWidget(QWidget):
    """Scatter plot with median and mean lines.

    ``points`` are ``(read_date, days, book_id)`` tuples; ``books`` maps
    book ids to ``(title, authors)`` for the tooltip; ``on_point_clicked``
    is called with a book id.
    """

    def __init__(self, points, date_format, parent=None, books=None,
                 colors=None, time_range='all', on_point_clicked=None):
        super().__init__(parent)
        self.points = points
        self.date_format = date_format
        self.books = books or {}
        self.on_point_clicked = on_point_clicked
        self.chrome = chrome_for(self)
        bg = self.chrome['background']
        rgb = (bg.red(), bg.green(), bg.blue())
        fixed = delay_colors(rgb)
        self.color_points = build_series_colors(
            is_dark_background(rgb), colors)['read']
        self.color_median = QColor(fixed['median'])
        self.color_mean = QColor(fixed['mean'])
        self._view = None          # None = auto-fit; else a View namedtuple
        self._press_pos = None     # pixel position of the mouse press
        self._pan_view = None      # view captured at the press
        self.setMinimumSize(700, 450)
        self.setMouseTracking(True)
        self.set_time_range(time_range)

    def set_time_range(self, time_range):
        """Selects the time range, recomputes its statistics and resets
        zoom/pan."""
        self.time_range = time_range
        self._view = None
        self.visible = []
        self.statistics = None
        if self.points:
            first, last = self.points[0][0], self.points[-1][0]
            x_min, x_max = fit_x_range(first, last, last, time_range)
            self.visible = [p for p in self.points
                            if x_min <= p[0] <= x_max]
            self.statistics = delay_statistics(self.visible)
        if self.statistics is not None:
            self.y_unit, self.y_factor, self.y_decimals = delay_unit(
                self.statistics['max'])
        self.update()

    # ------------------------------------------------------------------
    # Scaling
    # ------------------------------------------------------------------
    def _plot_rect(self):
        return QRectF(
            MARGIN_LEFT,
            MARGIN_TOP,
            max(50, self.width()  - MARGIN_LEFT - MARGIN_RIGHT),
            max(50, self.height() - MARGIN_TOP  - MARGIN_BOTTOM),
        )

    def _fit_view(self):
        """`View` showing all visible points, with a small margin."""
        x_min, x_max = self.visible[0][0], self.visible[-1][0]
        margin = timedelta(days=max(1, int((x_max - x_min).days
                                           * X_MARGIN_SHARE)))
        _, y_max = compute_y_axis(max(self.statistics['max'], 1)
                                  * self.y_factor)
        return View(x_min - margin, x_max + margin, y_max)

    def _current_view(self):
        return self._view if self._view is not None else self._fit_view()

    def _scale(self, plot):
        x_min, x_max, y_max = self._current_view()
        return PlotScale(plot, x_min, max(1, (x_max - x_min).days), y_max)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        try:
            self._do_paint()
        except Exception as e:
            show_paint_error(self, e)

    def _do_paint(self):
        painter = QPainter(self)
        painter.setRenderHint(RENDER_ANTIALIASING, True)
        painter.setRenderHint(RENDER_TEXT_ANTIALIASING, True)
        painter.fillRect(self.rect(), self.chrome['background'])

        if not self.visible:
            painter.setPen(self.chrome['text'])
            painter.drawText(self.rect(), ALIGN_CENTER,
                             _("No data available for this analysis."))
            painter.end()
            return

        plot = self._plot_rect()
        scale = self._scale(plot)
        y_step = nice_step(scale.y_max)

        self._draw_header(painter, plot)
        self._draw_axes(painter, scale, y_step)
        painter.save()
        painter.setClipRect(plot)
        self._draw_statistics_lines(painter, scale)
        self._draw_points(painter, scale)
        painter.restore()
        self._draw_line_labels(painter, scale)
        painter.end()

    def _draw_header(self, painter, plot):
        years = dict(TIME_RANGES).get(self.time_range)
        if years is None:
            title = _("Time between purchase and reading")
        else:
            title = _("Time between purchase and reading, last {years} "
                      "years").format(years=years)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(self.chrome['text'])
        painter.drawText(QRectF(plot.left(), 15, plot.width(), 30),
                         ALIGN_CENTER, title)

        s = self.statistics
        text = _(
            "Median: {med} days · Mean: {mean} days · "
            "Range: {min}–{max} days · n = {n}"
        ).format(
            med=int(round(s["median"])),
            mean=int(round(s["mean"])),
            min=s["min"],
            max=s["max"],
            n=s["count"],
        )
        font_stats = QFont()
        font_stats.setPointSize(11)
        painter.setFont(font_stats)
        painter.setPen(self.chrome['muted'])
        painter.drawText(QRectF(plot.left(), 50, plot.width(), 22),
                         ALIGN_CENTER, text)

    def _draw_axes(self, painter, scale, y_step):
        plot = scale.plot
        x_max = scale.x_min + timedelta(days=scale.x_days)
        painter.setPen(QPen(self.chrome['axis'], 1))
        painter.drawLine(QPointF(plot.left(),  plot.top()),
                         QPointF(plot.left(),  plot.bottom()))
        painter.drawLine(QPointF(plot.left(),  plot.bottom()),
                         QPointF(plot.right(), plot.bottom()))

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # Y axis
        y_value = 0.0
        while y_value <= scale.y_max + 0.001:
            y_pix = scale.value_to_y(y_value)
            pen = QPen(self.chrome['grid'], 1)
            pen.setStyle(PEN_DOT)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(),  y_pix),
                             QPointF(plot.right(), y_pix))

            painter.setPen(self.chrome['text'])
            text = f"{y_value:.{self.y_decimals}f}"
            width = fm.horizontalAdvance(text)
            painter.drawText(
                QRectF(plot.left() - 10 - width, y_pix - 8, width, 16),
                ALIGN_RIGHT | ALIGN_VCENTER, text,
            )
            y_value += y_step

        # X axis: years
        year_span = scale.x_days / 365.25
        step = year_tick_step(year_span)

        from datetime import date as _date
        for year in range(scale.x_min.year, x_max.year + 1):
            if year % step != 0:
                continue
            x_pix = scale.date_to_x(_date(year, 1, 1))
            if x_pix < plot.left() or x_pix > plot.right():
                continue
            painter.setPen(QPen(self.chrome['axis'], 1))
            painter.drawLine(QPointF(x_pix, plot.bottom()),
                             QPointF(x_pix, plot.bottom() + 5))
            painter.setPen(self.chrome['text'])
            t = str(year)
            b = fm.horizontalAdvance(t)
            painter.drawText(
                QRectF(x_pix - b / 2, plot.bottom() + 8, b, 18),
                ALIGN_CENTER, t,
            )

        # Axis titles
        title_font = QFont()
        title_font.setPointSize(11)
        painter.setFont(title_font)
        painter.setPen(self.chrome['text'])
        painter.drawText(
            QRectF(plot.left(), plot.bottom() + 28, plot.width(), 20),
            ALIGN_CENTER, _("Read on"),
        )

        y_label = {
            "days":   _("Days until read"),
            "months": _("Months until read"),
            "years":  _("Years until read"),
        }[self.y_unit]
        painter.save()
        painter.translate(22, plot.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot.height() / 2, -10, plot.height(), 20),
            ALIGN_CENTER, y_label,
        )
        painter.restore()

    def _statistic_lines(self, scale):
        """(y, label, color, style) of the median and mean lines."""
        s = self.statistics
        return [
            (scale.value_to_y(s["median"] * self.y_factor), _("Median"),
             self.color_median, PEN_DASH),
            (scale.value_to_y(s["mean"] * self.y_factor), _("Mean"),
             self.color_mean, PEN_DOT),
        ]

    def _draw_statistics_lines(self, painter, scale):
        plot = scale.plot
        for y, _label, color, style in self._statistic_lines(scale):
            pen = QPen(color, 2)
            pen.setStyle(style)
            if CAP_ROUND is not None:
                pen.setCapStyle(CAP_ROUND)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(), y),
                             QPointF(plot.right(), y))

    def _draw_line_labels(self, painter, scale):
        plot = scale.plot
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)
        for y, label, color, _style in self._statistic_lines(scale):
            if y < plot.top() or y > plot.bottom():
                continue
            tw = fm.horizontalAdvance(label) + 12
            th = fm.height() + 4
            box = QRectF(plot.left() + 8, y - th / 2, tw, th)
            painter.setPen(QPen(color, 1))
            painter.setBrush(QColor(*self.chrome['box_bg'], 235))
            painter.drawRoundedRect(box, 4, 4)
            painter.setPen(color)
            painter.drawText(box, ALIGN_CENTER, label)

    def _point_pos(self, scale, point):
        return QPointF(scale.date_to_x(point[0]),
                       scale.value_to_y(point[1] * self.y_factor))

    def _draw_points(self, painter, scale):
        color = QColor(self.color_points)
        color.setAlpha(150)
        painter.setPen(QPen(color, 1))
        painter.setBrush(color)
        for point in self.visible:
            painter.drawEllipse(self._point_pos(scale, point),
                                POINT_RADIUS, POINT_RADIUS)

    # ------------------------------------------------------------------
    # Interaction: zoom, pan, tooltips, click
    # ------------------------------------------------------------------
    def _point_at(self, pos):
        """Visible point nearest to ``pos`` within TOOLTIP_RADIUS."""
        plot = self._plot_rect()
        if not self.visible or not plot.contains(pos):
            return None
        scale = self._scale(plot)
        best, best_dist = None, TOOLTIP_RADIUS
        for point in self.visible:
            p = self._point_pos(scale, point)
            dist = ((p.x() - pos.x()) ** 2 + (p.y() - pos.y()) ** 2) ** 0.5
            if dist < best_dist:
                best, best_dist = point, dist
        return best

    def wheelEvent(self, event):
        try:
            delta = event.angleDelta().y()
            plot = self._plot_rect()
            if delta == 0 or not self.visible or plot.width() <= 0:
                return
            factor = ZOOM_IN_FACTOR if delta > 0 else ZOOM_OUT_FACTOR
            x_min, x_max, y_max = self._current_view()
            fit = self._fit_view()
            fx = min(max((_cursor_pos(event).x() - plot.left())
                         / plot.width(), 0.0), 1.0)
            self._view = zoom_view(x_min, x_max, y_max, fit.x_min,
                                   fit.x_max, fit.y_max, fx, factor)
            self.update()
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.visible:
            self._press_pos = _cursor_pos(event)
            self._pan_view = self._current_view()

    def mouseMoveEvent(self, event):
        pos = _cursor_pos(event)
        if self._press_pos is not None:
            self._pan_to(pos)
            self.update()
            return
        point = self._point_at(pos)
        if point is None:
            QToolTip.hideText()
            return
        title, authors = self.books.get(point[2], ('', ''))
        text = _("{title}\n{authors}\nRead on {date} · {days} days until "
                 "read\nClick to show it in calibre").format(
            title=title, authors=authors,
            date=point[0].strftime(self.date_format), days=point[1])
        QToolTip.showText(_global_pos(event), text, self)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self._press_pos is None:
            return
        pos = _cursor_pos(event)
        moved = abs(pos.x() - self._press_pos.x()) + \
            abs(pos.y() - self._press_pos.y())
        self._press_pos = None
        self._pan_view = None
        if moved >= CLICK_SLOP:
            return
        point = self._point_at(pos)
        if point is not None and self.on_point_clicked is not None:
            self.on_point_clicked(point[2])

    def mouseDoubleClickEvent(self, event):
        self._view = None
        self.update()

    def _pan_to(self, pos):
        x_min, x_max, y_max = self._pan_view
        plot = self._plot_rect()
        x_days = (x_max - x_min).days
        if plot.width() <= 0 or x_days <= 0:
            return
        shift_days = -(pos.x() - self._press_pos.x()) * x_days / plot.width()
        fit = self._fit_view()
        self._view = pan_view(x_min, x_max, y_max, fit.x_min, fit.x_max,
                              shift_days)


class DelayChartDialog(QDialog):
    """Dialog with the delay chart, time range, export buttons and Close.

    ``on_show(book_ids)`` displays books in calibre's book list; the
    dialog closes before it is called.
    """

    def __init__(self, points, date_format, parent=None, books=None,
                 colors=None, time_range='all', on_time_range_changed=None,
                 on_show=None):
        super().__init__(parent)
        self.on_show = on_show
        self.setWindowTitle(_("Time between purchase and reading"))
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        self.chart = DelayChartWidget(points, date_format, self, books=books,
                                      colors=colors, time_range=time_range,
                                      on_point_clicked=self._show)
        layout.addWidget(self.chart, 1)

        row = QHBoxLayout()
        add_time_range_box(self, row, self.chart, time_range,
                           on_time_range_changed)
        add_export_buttons(row, self.chart, 'delay')
        row.addStretch()
        row.addWidget(QLabel(_("Click a point to show the book in calibre."),
                             self))
        btn = QPushButton(_("Close"))
        btn.clicked.connect(self.reject)
        row.addWidget(btn)
        layout.addLayout(row)

    def _show(self, book_id):
        self.accept()
        if self.on_show is not None:
            self.on_show([book_id])
