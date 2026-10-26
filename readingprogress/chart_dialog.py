"""
Chart dialog for the ReadingProgress plugin.

Draws the burn-up chart directly with QPainter in a QWidget.
No external dependencies besides Qt (bundled with Calibre).
"""

import traceback
from datetime import date

from calibre.gui2 import choose_save_file, error_dialog
from calibre_plugins.readingprogress.chart_common import (
    DARK_DEFAULT_COLORS,
    DEFAULT_COLORS,
    TIME_RANGES,
    View,
    axis_ticks,
    chrome_colors,
    compute_y_axis,
    ensure_png_suffix,
    export_filename,
    fit_x_range,
    format_number,
    is_dark_background,
    nice_step,
    pan_view,
    resolve_series_colors,
    tick_decimals,
    visible_y_max,
    year_tick_step,
    zoom_view,
)
from calibre_plugins.readingprogress.export_reading_status import (
    compute_rates,
    required_pace,
)
from calibre_plugins.readingprogress.localization import _
from calibre_plugins.readingprogress.report import pace_line
from qt.core import (
    QApplication,
    QColor,
    QComboBox,
    QDialog,
    QFont,
    QFontMetrics,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPalette,
    QPen,
    QPoint,
    QPointF,
    QPushButton,
    QRectF,
    Qt,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

# Error log for paintEvent (for debugging)
LOG_ERROR = '/tmp/readingprogress_paint_error.log'


# Qt enums (calibre 8+ ships Qt 6, which only has the scoped names)
ALIGN_CENTER  = Qt.AlignmentFlag.AlignCenter
ALIGN_LEFT    = Qt.AlignmentFlag.AlignLeft
ALIGN_RIGHT   = Qt.AlignmentFlag.AlignRight
ALIGN_VCENTER = Qt.AlignmentFlag.AlignVCenter

PEN_SOLID   = Qt.PenStyle.SolidLine
PEN_DASH    = Qt.PenStyle.DashLine
PEN_DOT     = Qt.PenStyle.DotLine
PEN_DASHDOT = Qt.PenStyle.DashDotLine
PEN_NOPEN   = Qt.PenStyle.NoPen

CAP_ROUND  = Qt.PenCapStyle.RoundCap
JOIN_ROUND = Qt.PenJoinStyle.RoundJoin

LEFT_BUTTON = Qt.MouseButton.LeftButton

ELIDE_RIGHT = Qt.TextElideMode.ElideRight

RENDER_ANTIALIASING      = QPainter.RenderHint.Antialiasing
RENDER_TEXT_ANTIALIASING = QPainter.RenderHint.TextAntialiasing


# Plot area margins (in pixels)
MARGIN_LEFT    = 85
MARGIN_RIGHT   = 30
MARGIN_TOP     = 60
MARGIN_BOTTOM  = 60

# Required-pace lines below the burn-up title
PACE_LINE_TOP    = 46
PACE_LINE_HEIGHT = 20
PACE_MARGIN_TOP  = 105   # MARGIN_TOP with pace lines

# Interaction parameters
ZOOM_IN_FACTOR  = 1.25
ZOOM_OUT_FACTOR = 0.8
TOOLTIP_RADIUS  = 14.0


def _cursor_pos(event):
    """Cursor position of a mouse/wheel event as QPointF."""
    return event.position()


def _global_pos(event):
    """Global cursor position of a mouse event as QPoint."""
    return event.globalPosition().toPoint()


def chrome_for(widget):
    """Chrome QColor dict for ``widget``'s current palette (light/dark)."""
    bg = widget.palette().color(QPalette.ColorRole.Window)
    pal = chrome_colors((bg.red(), bg.green(), bg.blue()))
    return {
        'background': bg,
        'axis': QColor(pal['axis']),
        'grid': QColor(pal['grid']),
        'text': QColor(pal['text']),
        'border': QColor(pal['border']),
        'muted': QColor(pal['muted']),
        'error': QColor(pal['error']),
        'box_bg': pal['box_bg'],
    }


def show_paint_error(widget, error):
    """Logs the error to LOG_ERROR and draws a fallback message.

    Shared by all chart widgets so a drawing failure never crashes Calibre.
    """
    trace_text = traceback.format_exc()
    try:
        with open(LOG_ERROR, 'w', encoding='utf-8') as f:
            f.write(trace_text)
    except Exception:
        pass
    try:
        painter = QPainter(widget)
        chrome = chrome_for(widget)
        painter.fillRect(widget.rect(), chrome['background'])
        painter.setPen(QPen(chrome['error'], 1))
        message = _("Error drawing:\n{type}: {error}\n\nDetails: {log}").format(
            type=type(error).__name__, error=error, log=LOG_ERROR)
        painter.drawText(widget.rect(), ALIGN_CENTER, message)
        painter.end()
    except Exception:
        pass


def build_series_colors(dark, overrides):
    """QColor per series key: user overrides, else the theme default."""
    result = {}
    for key, hex_val in resolve_series_colors(dark, overrides).items():
        color = QColor(hex_val)
        if not color.isValid():
            color = QColor(DARK_DEFAULT_COLORS[key] if dark
                           else DEFAULT_COLORS[key])
        result[key] = color
    return result


def save_chart_png(widget, kind):
    """Asks for a file name and saves ``widget`` as currently shown."""
    path = choose_save_file(
        widget, 'readingprogress-export-png', _("Save chart as PNG"),
        filters=[(_("PNG images"), ['png'])], all_files=False,
        initial_filename=export_filename(kind))
    if not path:
        return
    path = ensure_png_suffix(path)
    if not widget.grab().save(path, 'PNG'):
        error_dialog(widget, _("Export failed"),
                     _("Could not write {path}.").format(path=path),
                     show=True)


def copy_chart_to_clipboard(widget, button):
    """Copies ``widget`` as currently shown to the clipboard as an image."""
    QApplication.clipboard().setPixmap(widget.grab())
    QToolTip.showText(button.mapToGlobal(QPoint(0, button.height())),
                      _("Chart copied to clipboard"), button)


def add_export_buttons(row, widget, kind):
    """Adds 'Save as PNG…' and 'Copy to clipboard' buttons to ``row``.

    ``kind`` names the chart in the suggested file name.
    """
    save_btn = QPushButton(_("Save as PNG…"))
    save_btn.clicked.connect(lambda: save_chart_png(widget, kind))
    row.addWidget(save_btn)

    copy_btn = QPushButton(_("Copy to clipboard"))
    copy_btn.clicked.connect(
        lambda: copy_chart_to_clipboard(widget, copy_btn))
    row.addWidget(copy_btn)


def add_time_range_box(parent, row, chart, time_range, on_changed):
    """Adds the 'Time range' selector to ``row``.

    Switching calls ``chart.set_time_range(key)`` and ``on_changed(key)``
    (which persists the choice; may be ``None``).
    """
    labels = {
        'all': _("All time"),
        '5y': _("Last 5 years"),
        '2y': _("Last 2 years"),
    }
    box = QComboBox(parent)
    for key, _years in TIME_RANGES:
        box.addItem(labels[key], key)
    index = box.findData(time_range)
    box.setCurrentIndex(index if index >= 0 else 0)

    def changed(index):
        key = box.itemData(index)
        chart.set_time_range(key)
        if on_changed is not None:
            on_changed(key)

    box.currentIndexChanged.connect(changed)
    row.addWidget(QLabel(_("Time range:"), parent))
    row.addWidget(box)


class PlotScale:
    """Maps data coordinates to pixel coordinates."""

    def __init__(self, plot, x_min, x_days, y_max):
        self.plot = plot
        self.x_min = x_min
        self.x_days = x_days
        self.y_max = y_max

    def date_to_x(self, date):
        days = (date - self.x_min).days
        return self.plot.left() + self.plot.width() * days / self.x_days

    def value_to_y(self, value):
        return self.plot.bottom() - self.plot.height() * value / self.y_max


class AxesRenderer:
    """Draws axes, grid, tick labels and axis titles."""

    def draw(self, painter, scale, x_max, y_max, y_step, chrome,
             y_title=None, x_title=None, decimal_sep='.'):
        """``y_title``/``x_title`` default to "Number of books"/"Year".
        Tick labels get as many decimals as ``y_step`` needs."""
        plot = scale.plot
        painter.setPen(QPen(chrome['axis'], 1))
        painter.drawLine(QPointF(plot.left(),  plot.top()),
                         QPointF(plot.left(),  plot.bottom()))
        painter.drawLine(QPointF(plot.left(),  plot.bottom()),
                         QPointF(plot.right(), plot.bottom()))

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # Y axis
        decimals = tick_decimals(y_step)
        for y_value in axis_ticks(y_max, y_step):
            y_pix = scale.value_to_y(y_value)
            pen = QPen(chrome['grid'], 1)
            pen.setStyle(PEN_DOT)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(),  y_pix),
                             QPointF(plot.right(), y_pix))
            painter.setPen(chrome['text'])
            text = format_number(y_value, decimals, decimal_sep)
            width = fm.horizontalAdvance(text)
            painter.drawText(
                QRectF(plot.left() - 10 - width, y_pix - 8, width, 16),
                ALIGN_RIGHT | ALIGN_VCENTER, text,
            )

        # X axis: year markers
        year_span = (x_max - scale.x_min).days / 365.25
        step = year_tick_step(year_span)

        for year in range(scale.x_min.year + 1, x_max.year + 1):
            if year % step != 0:
                continue
            x_pix = scale.date_to_x(date(year, 1, 1))
            if x_pix < plot.left() or x_pix > plot.right():
                continue
            painter.setPen(QPen(chrome['axis'], 1))
            painter.drawLine(QPointF(x_pix, plot.bottom()),
                             QPointF(x_pix, plot.bottom() + 5))
            painter.setPen(chrome['text'])
            text = str(year)
            width = fm.horizontalAdvance(text)
            painter.drawText(
                QRectF(x_pix - width / 2, plot.bottom() + 8, width, 18),
                ALIGN_CENTER, text,
            )

        # Axis titles
        title_font = QFont()
        title_font.setPointSize(11)
        painter.setFont(title_font)
        painter.setPen(chrome['text'])
        painter.drawText(
            QRectF(plot.left(), plot.bottom() + 28, plot.width(), 20),
            ALIGN_CENTER, x_title or _("Year"),
        )

        painter.save()
        painter.translate(20, plot.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot.height() / 2, -10, plot.height(), 20),
            ALIGN_CENTER, y_title or _("Number of books"),
        )
        painter.restore()


class SeriesRenderer:
    """Draws data series and target/reference lines."""

    def draw_series(self, painter, scale, rows, index, color, width):
        pen = QPen(color, width)
        pen.setCapStyle(CAP_ROUND)
        pen.setJoinStyle(JOIN_ROUND)
        painter.setPen(pen)

        points = []
        for row in rows:
            x = scale.date_to_x(row[0])
            y = scale.value_to_y(row[index])
            points.append(QPointF(x, y))

        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

    def draw_reference_line(self, painter, scale, start, end, color, style,
                            width):
        pen = QPen(color, width)
        pen.setStyle(style)
        pen.setCapStyle(CAP_ROUND)
        painter.setPen(pen)

        x1 = scale.date_to_x(start[0])
        y1 = scale.value_to_y(start[1])
        x2 = scale.date_to_x(end[0])
        y2 = scale.value_to_y(end[1])

        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


class AnnotationRenderer:
    """Draws the title and the 'Today' annotation."""

    def draw_title(self, painter, plot, rows, target_date, reduction_factor,
                   date_format, chrome, years=None):
        """``years`` = length of a limited time range; such a view ends
        today, so the title names the range instead of the goal."""
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(chrome['text'])

        if years is not None:
            title = _("Reading progress over the last {years} years").format(
                years=years)
        else:
            current_backlog = rows[-1][3]
            target_soft_i = round(current_backlog * reduction_factor)
            date_str = target_date.strftime(date_format)
            title = _("Reading progress for TBR = {tbr} on {date}").format(
                tbr=target_soft_i, date=date_str)
        painter.drawText(
            QRectF(plot.left(), 15, plot.width(), 30),
            ALIGN_CENTER, title,
        )

    def draw_pace(self, painter, plot, widget_width, lines, chrome):
        """Required-pace sentences, one per line, below the title.

        Centered over ``plot`` like the title; too long for it, they use
        the whole widget width, shrink down to 8 pt and are elided last."""
        if not lines:
            return
        font = QFont()
        for size in range(11, 7, -1):
            font.setPointSize(size)
            fm = QFontMetrics(font)
            needed = max(fm.horizontalAdvance(t) for t in lines)
            if needed <= widget_width - 20:
                break
        if needed <= plot.width():
            left, width = plot.left(), plot.width()
        else:
            left, width = 10, widget_width - 20
        painter.setFont(font)
        painter.setPen(chrome['muted'])
        for i, text in enumerate(lines):
            painter.drawText(
                QRectF(left, PACE_LINE_TOP + i * PACE_LINE_HEIGHT,
                       width, PACE_LINE_HEIGHT),
                ALIGN_CENTER, fm.elidedText(text, ELIDE_RIGHT, int(width)))

    def draw_today(self, painter, scale, today, current_backlog,
                   backlog_color, chrome):
        x = scale.date_to_x(today)
        y = scale.value_to_y(current_backlog)

        painter.setPen(QPen(backlog_color, 1))
        painter.setBrush(backlog_color)
        painter.drawEllipse(QPointF(x, y), 5, 5)

        text = _("Today: {count} unread").format(count=current_backlog)
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text) + 16
        th = fm.height() + 10

        plot = scale.plot
        if x + tw + 20 < plot.right():
            bx = x + 15
        else:
            bx = x - tw - 15
        by = y - th - 15
        if by < plot.top() + 5:
            by = y + 15

        box = QRectF(bx, by, tw, th)
        painter.setBrush(QColor(*chrome['box_bg'], 235))
        painter.setPen(QPen(chrome['border'], 1))
        painter.drawRoundedRect(box, 5, 5)

        painter.setPen(chrome['text'])
        painter.drawText(box, ALIGN_CENTER, text)

        painter.setPen(QPen(chrome['axis'], 1))
        start = QPointF(box.left() + 5 if bx > x else box.right() - 5,
                        box.center().y())
        painter.drawLine(start, QPointF(x, y))

    def draw_forecast_note(self, painter, scale, date, date_format,
                           x_end, y_end, chrome):
        """Small label near the end of the forecast line."""
        plot = scale.plot
        text = _("Realistic: TBR = 0 on {date}").format(
            date=date.strftime(date_format))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text) + 16
        th = fm.height() + 10

        bx = x_end - tw / 2
        by = y_end - th - 15
        if bx < plot.left():
            bx = plot.left() + 4
        if bx + tw > plot.right():
            bx = plot.right() - tw - 4
        if by < plot.top() + 4:
            by = y_end + 15

        box = QRectF(bx, by, tw, th)
        painter.setBrush(QColor(*chrome['box_bg'], 235))
        painter.setPen(QPen(chrome['border'], 1))
        painter.drawRoundedRect(box, 5, 5)
        painter.setPen(chrome['text'])
        painter.drawText(box, ALIGN_CENTER, text)


class LegendRenderer:
    """Draws the legend."""

    def draw(self, painter, plot, target_date, date_format, target_soft,
             show_forecast=False, colors=None, chrome=None,
             show_reference=True):
        """``show_reference=False`` lists only the data series, for a
        view that ends today and so shows no goal/forecast lines."""
        date_str = target_date.strftime(date_format)
        year_str = target_date.strftime('%Y')
        target_soft_i = round(target_soft)

        entries = [
            (_("Total library"), colors['total'], PEN_SOLID),
            (_("Read (cumulative)"), colors['read'], PEN_SOLID),
            (_("Backlog (TBR)"), colors['backlog'], PEN_SOLID),
        ]
        reference_entries = [
            (_("Goal: TBR = 0 on {date}").format(date=date_str),
             colors['goal'], PEN_DASH),
            (_("Constant library (buy rate = read rate)"),
             colors['stable'], PEN_DOT),
            (_("Gentle reduction to TBR = {tbr} by {year}").format(
                tbr=target_soft_i, year=year_str),
             colors['soft'], PEN_DASHDOT),
        ]
        if show_forecast:
            reference_entries.append((_("Forecast (last 12 months)"),
                                      colors['forecast'], PEN_DASH))
        if show_reference:
            entries += reference_entries
        self.draw_entries(painter, plot, entries, chrome)

    def draw_entries(self, painter, plot, entries, chrome):
        """Draws a legend box in the top right corner of ``plot``.

        ``entries`` are ``(text, color, pen_style)``; a ``pen_style`` of
        ``None`` draws a filled swatch instead of a line.
        """
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        line_width = 30
        padding = 10
        row_height = fm.height() + 6
        max_text_width = max(fm.horizontalAdvance(e[0]) for e in entries)
        box_width = padding * 2 + line_width + 8 + max_text_width
        box_height = padding * 2 + row_height * len(entries)

        box_x = plot.right() - box_width - 10
        box_y = plot.top() + 10

        painter.setPen(QPen(chrome['border'], 1))
        painter.setBrush(QColor(*chrome['box_bg'], 230))
        painter.drawRoundedRect(
            QRectF(box_x, box_y, box_width, box_height), 5, 5)

        for i, (text, color, style) in enumerate(entries):
            row_y = box_y + padding + i * row_height + row_height / 2
            if style is None:
                painter.setPen(QPen(PEN_NOPEN))
                painter.setBrush(color)
                painter.drawRect(QRectF(box_x + padding, row_y - 5,
                                        line_width, 10))
            else:
                pen = QPen(color, 2.5)
                pen.setStyle(style)
                painter.setPen(pen)
                painter.drawLine(
                    QPointF(box_x + padding, row_y),
                    QPointF(box_x + padding + line_width, row_y),
                )
            painter.setPen(chrome['text'])
            painter.drawText(
                QRectF(box_x + padding + line_width + 8,
                       row_y - row_height / 2,
                       max_text_width, row_height),
                ALIGN_LEFT | ALIGN_VCENTER, text,
            )


class ChartWidget(QWidget):
    """Draws the burn-up chart; holds only the orchestration."""

    def __init__(self, rows, target_date, reduction_factor, date_format,
                 parent=None, show_forecast=True, forecast=None, colors=None,
                 time_range='all', decimal_sep='.'):
        super().__init__(parent)
        self.rows = rows
        self.target_date = target_date
        self.reduction_factor = reduction_factor
        self.date_format = date_format
        self.show_forecast = show_forecast
        self.forecast = forecast
        self.chrome = chrome_for(self)
        bg = self.chrome['background']
        self._dark = is_dark_background((bg.red(), bg.green(), bg.blue()))
        self.colors = self._build_colors(colors)
        self.time_range = time_range
        self.pace_lines = self._pace_lines(decimal_sep)
        self._view = None          # None = auto-fit; else a View namedtuple
        self._pan_start = None     # pixel position while panning
        self._pan_view = None      # view captured at drag start
        self._axes = AxesRenderer()
        self._series = SeriesRenderer()
        self._legend = LegendRenderer()
        self._annotation = AnnotationRenderer()
        self.setMinimumSize(700, 450)
        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Drawing (with error handling, so an error does not kill Calibre)
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

        if not self.rows or len(self.rows) < 2:
            painter.setPen(self.chrome['text'])
            painter.drawText(self.rect(), ALIGN_CENTER, _("No data"))
            painter.end()
            return

        plot = self._plot_rect()

        if self._view is None:
            x_min, x_max = self._fit_x_range()
            y_step, y_max = compute_y_axis(self._data_y_max(), integer=True)
        else:
            x_min = self._view.x_min
            x_max = self._view.x_max
            y_max = self._view.y_max
            y_step = nice_step(y_max, integer=True)
        x_days = (x_max - x_min).days
        if x_days <= 0:
            painter.end()
            return

        scale = PlotScale(plot, x_min, x_days, y_max)

        self._axes.draw(painter, scale, x_max, y_max, y_step, self.chrome)
        self._annotation.draw_title(painter, plot, self.rows,
                                    self.target_date, self.reduction_factor,
                                    self.date_format, self.chrome,
                                    years=dict(TIME_RANGES).get(
                                        self.time_range))
        self._annotation.draw_pace(painter, plot, self.width(),
                                   self.pace_lines, self.chrome)

        current_backlog = self.rows[-1][3]
        today = self.rows[-1][0]
        target_soft = current_backlog * self.reduction_factor

        # Lines outside the visible window (zoom, time range) must not
        # spill into the margins.
        painter.save()
        painter.setClipRect(plot)
        self._series.draw_reference_line(
            painter, scale, start=(today, current_backlog),
            end=(self.target_date, 0),
            color=self.colors['goal'], style=PEN_DASH, width=2,
        )
        self._series.draw_reference_line(
            painter, scale, start=(today, current_backlog),
            end=(self.target_date, target_soft),
            color=self.colors['soft'], style=PEN_DASHDOT, width=2,
        )
        self._series.draw_reference_line(
            painter, scale, start=(today, current_backlog),
            end=(self.target_date, current_backlog),
            color=self.colors['stable'], style=PEN_DOT, width=2,
        )

        self._series.draw_series(painter, scale, self.rows,
                                 index=1, color=self.colors['total'], width=2)
        self._series.draw_series(painter, scale, self.rows,
                                 index=2, color=self.colors['read'], width=2.5)
        self._series.draw_series(painter, scale, self.rows,
                                 index=3, color=self.colors['backlog'],
                                 width=3)

        if self.show_forecast:
            self._draw_forecast(painter, scale)
        painter.restore()

        if self.show_forecast:
            self._draw_forecast_note(painter, scale)

        self._annotation.draw_today(painter, scale, today, current_backlog,
                                    self.colors['backlog'], self.chrome)
        self._legend.draw(painter, plot, self.target_date, self.date_format,
                           target_soft, self.show_forecast, self.colors,
                           self.chrome, show_reference=x_max > today)

        painter.end()

    def _forecast_end(self):
        """(end_date, end_y) of the forecast line, or None."""
        fc = self.forecast
        if not fc or not fc.get('ok'):
            return None
        slope = fc['slope']
        intercept = fc['intercept']
        anchor = fc['anchor']
        zero_date = fc['zero_date']

        if slope < 0 and zero_date is not None and \
                zero_date <= self.target_date:
            end_date = zero_date
            end_y = 0.0
        else:
            end_date = self.target_date
            end_y = intercept + slope * (end_date - anchor).days
            if end_y < 0:
                end_y = 0.0
        return end_date, end_y

    def _draw_forecast(self, painter, scale):
        """Draws the forecast line."""
        end = self._forecast_end()
        if end is None:
            return
        self._series.draw_reference_line(
            painter, scale,
            start=(self.forecast['anchor'], self.forecast['intercept']),
            end=end,
            color=self.colors['forecast'], style=PEN_DASH, width=2)

    def _draw_forecast_note(self, painter, scale):
        """Draws the 'realistic' zero-date note at the end of the forecast
        line, if that end lies inside the visible window."""
        end = self._forecast_end()
        if end is None or self.forecast['zero_date'] is None:
            return
        end_date, end_y = end
        x_end = scale.date_to_x(end_date)
        plot = scale.plot
        if x_end < plot.left() or x_end > plot.right():
            return
        y_end = scale.value_to_y(end_y)
        self._annotation.draw_forecast_note(
            painter, scale, self.forecast['zero_date'], self.date_format,
            x_end, y_end, self.chrome)

    # ------------------------------------------------------------------
    # Scaling / view helpers
    # ------------------------------------------------------------------
    def _build_colors(self, overrides):
        return build_series_colors(self._dark, overrides)

    def _plot_rect(self):
        top = PACE_MARGIN_TOP if self.pace_lines else MARGIN_TOP
        return QRectF(
            MARGIN_LEFT,
            top,
            max(50, self.width()  - MARGIN_LEFT - MARGIN_RIGHT),
            max(50, self.height() - top - MARGIN_BOTTOM),
        )

    def _pace_lines(self, decimal_sep):
        """Required-pace sentences for TBR = 0 and, if it is a different
        goal, the gentle reduction. They do not depend on the visible
        window, so they stay for every time range."""
        if not self.rows or len(self.rows) < 2:
            return []
        today, backlog = self.rows[-1][0], self.rows[-1][3]
        rates = compute_rates(self.rows)
        targets = [0]
        soft = round(backlog * self.reduction_factor)
        if soft != 0:
            targets.append(soft)
        date_str = self.target_date.strftime(self.date_format)
        return [pace_line(required_pace(backlog, rates, today,
                                        self.target_date, target),
                          _, date_str, decimal_sep)
                for target in targets]

    def _fit_x_range(self):
        """(x_min, x_max) of the unzoomed view for the time range."""
        return fit_x_range(self.rows[0][0], self.rows[-1][0],
                           self.target_date, self.time_range)

    def _data_y_max(self):
        """Largest value within the time range (ignoring zoom)."""
        return visible_y_max(self.rows, *self._fit_x_range())

    def _current_view(self):
        """`View` of the current, possibly zoomed view."""
        if self._view is not None:
            return self._view
        _step, y_max = compute_y_axis(self._data_y_max(), integer=True)
        return View(*self._fit_x_range(), y_max)

    def set_time_range(self, time_range):
        """Switches the time range and resets zoom/pan."""
        self.time_range = time_range
        self._view = None
        self.update()

    def _scale_for(self, plot):
        x_min, x_max, y_max = self._current_view()
        x_days = (x_max - x_min).days
        if x_days <= 0:
            x_days = 1
        return PlotScale(plot, x_min, x_days, y_max)

    # ------------------------------------------------------------------
    # Interaction: zoom, pan, tooltips
    # ------------------------------------------------------------------
    def wheelEvent(self, event):
        try:
            delta = event.angleDelta().y()
            if delta == 0:
                return
            self._zoom_at(_cursor_pos(event), ZOOM_IN_FACTOR if delta > 0 else ZOOM_OUT_FACTOR)
            self.update()
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == LEFT_BUTTON:
            self._pan_start = _cursor_pos(event)
            self._pan_view = self._current_view()

    def mouseMoveEvent(self, event):
        if self._pan_start is not None:
            self._pan_to(_cursor_pos(event))
            self.update()
        else:
            self._show_tooltip(event)

    def mouseReleaseEvent(self, event):
        if event.button() == LEFT_BUTTON:
            self._pan_start = None
            self._pan_view = None

    def mouseDoubleClickEvent(self, event):
        self._view = None
        self.update()

    def _zoom_at(self, pos, factor):
        """factor > 1 zooms in (narrower range), < 1 zooms out."""
        plot = self._plot_rect()
        if plot.width() <= 0 or plot.height() <= 0:
            return
        x_min, x_max, y_max = self._current_view()
        fit_x_min, fit_x_max = self._fit_x_range()
        _step, fit_y_max = compute_y_axis(self._data_y_max(), integer=True)

        fx = min(max((pos.x() - plot.left()) / plot.width(), 0.0), 1.0)

        self._view = zoom_view(
            x_min, x_max, y_max, fit_x_min, fit_x_max, fit_y_max, fx, factor)

    def _pan_to(self, pos):
        if self._pan_start is None or self._pan_view is None:
            return
        x_min, x_max, y_max = self._pan_view
        plot = self._plot_rect()
        if plot.width() <= 0:
            return
        x_days = (x_max - x_min).days
        if x_days <= 0:
            return
        days_per_pixel = x_days / plot.width()
        shift_days = -(pos.x() - self._pan_start.x()) * days_per_pixel

        self._view = pan_view(
            x_min, x_max, y_max, *self._fit_x_range(), shift_days)

    def _show_tooltip(self, event):
        pos = _cursor_pos(event)
        plot = self._plot_rect()
        if not plot.contains(pos):
            QToolTip.hideText()
            return
        scale = self._scale_for(plot)

        best = None
        best_dist = TOOLTIP_RADIUS
        for row in self.rows:
            dist = abs(scale.date_to_x(row[0]) - pos.x())
            if dist < best_dist:
                best_dist = dist
                best = row
        if best is None:
            QToolTip.hideText()
            return

        text = _("{date}\nTotal: {total}\nRead: {read}\nBacklog: {backlog}") \
            .format(date=best[0].strftime(self.date_format),
                    total=best[1], read=best[2], backlog=best[3])
        QToolTip.showText(_global_pos(event), text, self)


class ChartDialog(QDialog):
    """Dialog that holds the chart widget, export buttons and Close."""

    def __init__(self, rows, target_date, reduction_factor, date_format,
                 parent=None, show_forecast=True, forecast=None, colors=None,
                 time_range='all', on_time_range_changed=None,
                 decimal_sep='.'):
        super().__init__(parent)
        self.setWindowTitle(_("Reading progress"))
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        self.chart = ChartWidget(rows, target_date, reduction_factor,
                                 date_format, self,
                                 show_forecast=show_forecast,
                                 forecast=forecast, colors=colors,
                                 time_range=time_range,
                                 decimal_sep=decimal_sep)
        layout.addWidget(self.chart, 1)

        row = QHBoxLayout()
        add_time_range_box(self, row, self.chart, time_range,
                           on_time_range_changed)
        add_export_buttons(row, self.chart, 'burn-up')
        row.addStretch()
        btn = QPushButton(_("Close"))
        btn.clicked.connect(self.reject)
        row.addWidget(btn)
        layout.addLayout(row)
