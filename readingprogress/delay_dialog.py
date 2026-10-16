"""
Dialog for the reading-delay analysis.

Shows a scatter plot: x-axis = when it was read, y-axis = how many days
the book sat unread on the shelf. Horizontal lines mark the median and
mean.
"""

import traceback

from calibre_plugins.readingprogress.chart_dialog import (
    ALIGN_CENTER,
    ALIGN_RIGHT,
    ALIGN_VCENTER,
    CAP_ROUND,
    LOG_ERROR,
    PEN_DASH,
    PEN_DOT,
    RENDER_ANTIALIASING,
    RENDER_TEXT_ANTIALIASING,
)
from calibre_plugins.readingprogress.localization import _
from qt.core import (
    QColor,
    QDialog,
    QFont,
    QFontMetrics,
    QHBoxLayout,
    QPainter,
    QPen,
    QPointF,
    QPushButton,
    QRectF,
    QVBoxLayout,
    QWidget,
)


class DelayChartWidget(QWidget):
    """Scatter plot with median and mean lines."""

    COLOR_POINTS = QColor("#2a9d8f")
    COLOR_MEDIAN = QColor("#264653")
    COLOR_MEAN   = QColor("#f4a261")
    COLOR_AXIS   = QColor("#333333")
    COLOR_GRID   = QColor("#e0e0e0")
    COLOR_TEXT   = QColor("#222222")

    MARGIN_LEFT    = 95
    MARGIN_RIGHT   = 30
    MARGIN_TOP     = 95
    MARGIN_BOTTOM  = 65

    def __init__(self, points, statistics, date_format, language,
                 parent=None):
        super().__init__(parent)
        self.points = points
        self.statistics = statistics
        self.date_format = date_format
        self.language = language
        self.setMinimumSize(700, 450)

        # Adapt the Y unit to the magnitude
        max_days = statistics["max"]
        if max_days <= 90:
            self.y_unit = "days"
            self.y_factor = 1.0
            self.y_decimals = 0
        elif max_days <= 730:
            self.y_unit = "months"
            self.y_factor = 1.0 / 30.44
            self.y_decimals = 0
        else:
            self.y_unit = "years"
            self.y_factor = 1.0 / 365.25
            self.y_decimals = 1

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        try:
            self._do_paint()
        except Exception as e:
            error = traceback.format_exc()
            try:
                with open(LOG_ERROR, 'w', encoding='utf-8') as f:
                    f.write(error)
            except Exception:
                pass
            try:
                painter = QPainter(self)
                painter.fillRect(self.rect(), QColor("#ffffff"))
                painter.setPen(QPen(QColor("#cc0000"), 1))
                message = _(
                    "Error drawing:\n{type}: {error}\n\nDetails: {log}"
                ).format(type=type(e).__name__, error=e, log=LOG_ERROR)
                painter.drawText(self.rect(), ALIGN_CENTER, message)
                painter.end()
            except Exception:
                pass

    def _do_paint(self):
        painter = QPainter(self)
        painter.setRenderHint(RENDER_ANTIALIASING, True)
        painter.setRenderHint(RENDER_TEXT_ANTIALIASING, True)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        if not self.points:
            painter.setPen(self.COLOR_TEXT)
            painter.drawText(self.rect(), ALIGN_CENTER,
                             _("No data available for this analysis."))
            painter.end()
            return

        plot = QRectF(
            self.MARGIN_LEFT,
            self.MARGIN_TOP,
            max(50, self.width()  - self.MARGIN_LEFT - self.MARGIN_RIGHT),
            max(50, self.height() - self.MARGIN_TOP  - self.MARGIN_BOTTOM),
        )

        # X range: earliest to latest read date + small margin
        x_min_d = self.points[0][0]
        x_max_d = self.points[-1][0]
        span = (x_max_d - x_min_d).days
        if span <= 0:
            span = 1
        margin = max(1, int(span * 0.02))
        from datetime import timedelta
        x_min_d = x_min_d - timedelta(days=margin)
        x_max_d = x_max_d + timedelta(days=margin)
        x_span = (x_max_d - x_min_d).days

        # Y range in days; then convert to the chosen unit
        y_max_days = max(self.statistics["max"], 1)
        y_max_unit = y_max_days * self.y_factor
        y_step, y_max = self._compute_y_axis(y_max_unit)

        # Title and key figures
        self._draw_header(painter, plot)

        # Axes and grid
        self._draw_axes(painter, plot, x_min_d, x_max_d, x_span,
                        y_max, y_step)

        # Statistics lines
        self._draw_statistics_lines(painter, plot, y_max)

        # Data points (front)
        self._draw_points(painter, plot, x_min_d, x_span,
                          y_max)

        painter.end()

    # ------------------------------------------------------------------
    def _compute_y_axis(self, max_value):
        import math
        if max_value <= 0:
            return 1, 1
        raw = max_value / 5.0
        magnitude = 10 ** math.floor(math.log10(raw))
        step = magnitude
        for factor in (1, 2, 2.5, 5, 10):
            step = factor * magnitude
            if step >= raw:
                break
        y_max = math.ceil(max_value / step) * step
        return step, y_max

    def _date_to_x(self, date, x_min, x_span, plot):
        days = (date - x_min).days
        return plot.left() + plot.width() * days / x_span

    def _value_to_y(self, value, y_max, plot):
        return plot.bottom() - plot.height() * value / y_max

    # ------------------------------------------------------------------
    def _draw_header(self, painter, plot):
        # Title
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(self.COLOR_TEXT)
        painter.drawText(
            QRectF(plot.left(), 15, plot.width(), 30),
            ALIGN_CENTER, _("Time between purchase and reading"),
        )

        # Key figures line
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
        painter.setPen(QColor("#555555"))
        painter.drawText(
            QRectF(plot.left(), 50, plot.width(), 22),
            ALIGN_CENTER, text,
        )

    # ------------------------------------------------------------------
    def _draw_axes(self, painter, plot, x_min_d, x_max_d, x_span,
                        y_max, y_step):
        painter.setPen(QPen(self.COLOR_AXIS, 1))
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
        while y_value <= y_max + 0.001:
            y_pix = self._value_to_y(y_value, y_max, plot)
            pen = QPen(self.COLOR_GRID, 1)
            pen.setStyle(PEN_DOT)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(),  y_pix),
                             QPointF(plot.right(), y_pix))

            painter.setPen(self.COLOR_TEXT)
            text = f"{y_value:.{self.y_decimals}f}"
            width = fm.horizontalAdvance(text)
            painter.drawText(
                QRectF(plot.left() - 10 - width, y_pix - 8, width, 16),
                ALIGN_RIGHT | ALIGN_VCENTER, text,
            )
            y_value += y_step

        # X axis: years
        year_span = (x_max_d - x_min_d).days / 365.25
        if year_span <= 5:
            step = 1
        elif year_span <= 15:
            step = 2
        elif year_span <= 40:
            step = 5
        else:
            step = 10

        from datetime import date as _date
        for year in range(x_min_d.year, x_max_d.year + 1):
            if year % step != 0:
                continue
            try:
                d = _date(year, 1, 1)
            except ValueError:
                continue
            x_pix = self._date_to_x(d, x_min_d, x_span, plot)
            if x_pix < plot.left() or x_pix > plot.right():
                continue
            painter.setPen(QPen(self.COLOR_AXIS, 1))
            painter.drawLine(QPointF(x_pix, plot.bottom()),
                             QPointF(x_pix, plot.bottom() + 5))
            painter.setPen(self.COLOR_TEXT)
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
        painter.setPen(self.COLOR_TEXT)

        # X axis title
        painter.drawText(
            QRectF(plot.left(), plot.bottom() + 28, plot.width(), 20),
            ALIGN_CENTER, _("Read on"),
        )

        # Y axis title (rotated)
        y_label_map = {
            "days":   _("Days until read"),
            "months": _("Months until read"),
            "years":  _("Years until read"),
        }
        y_label = y_label_map[self.y_unit]
        painter.save()
        painter.translate(22, plot.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot.height() / 2, -10, plot.height(), 20),
            ALIGN_CENTER, y_label,
        )
        painter.restore()

    # ------------------------------------------------------------------
    def _draw_statistics_lines(self, painter, plot, y_max):
        # Median
        median_unit = self.statistics["median"] * self.y_factor
        y_med = self._value_to_y(median_unit, y_max, plot)
        pen = QPen(self.COLOR_MEDIAN, 2)
        pen.setStyle(PEN_DASH)
        if CAP_ROUND is not None:
            pen.setCapStyle(CAP_ROUND)
        painter.setPen(pen)
        painter.drawLine(QPointF(plot.left(), y_med),
                         QPointF(plot.right(), y_med))

        # Mean
        mean_unit = self.statistics["mean"] * self.y_factor
        y_mean = self._value_to_y(mean_unit, y_max, plot)
        pen = QPen(self.COLOR_MEAN, 2)
        pen.setStyle(PEN_DOT)
        if CAP_ROUND is not None:
            pen.setCapStyle(CAP_ROUND)
        painter.setPen(pen)
        painter.drawLine(QPointF(plot.left(), y_mean),
                         QPointF(plot.right(), y_mean))

        # Labels on the right side
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        self._draw_line_label(
            painter, plot, y_med, _("Median"),
            self.COLOR_MEDIAN, fm)
        self._draw_line_label(
            painter, plot, y_mean, _("Mean"),
            self.COLOR_MEAN, fm)

    def _draw_line_label(self, painter, plot, y, text, color, fm):
        tw = fm.horizontalAdvance(text) + 12
        th = fm.height() + 4
        box = QRectF(plot.left() + 8, y - th / 2, tw, th)
        painter.setPen(QPen(color, 1))
        painter.setBrush(QColor(255, 255, 255, 235))
        painter.drawRoundedRect(box, 4, 4)
        painter.setPen(color)
        painter.drawText(box, ALIGN_CENTER, text)

    # ------------------------------------------------------------------
    def _draw_points(self, painter, plot, x_min, x_span, y_max):
        color = QColor(self.COLOR_POINTS)
        color.setAlpha(150)
        painter.setPen(QPen(color, 1))
        painter.setBrush(color)
        for read_date, days, _id in self.points:
            x = self._date_to_x(read_date, x_min, x_span, plot)
            y_unit = days * self.y_factor
            y = self._value_to_y(y_unit, y_max, plot)
            if y < plot.top() - 2 or y > plot.bottom() + 2:
                continue
            painter.drawEllipse(QPointF(x, y), 3.5, 3.5)


class DelayChartDialog(QDialog):
    """Dialog that shows the delay chart and a Close button."""

    def __init__(self, points, statistics, date_format, language,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Time between purchase and reading"))
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        self.chart = DelayChartWidget(points, statistics, date_format,
                                      language, self)
        layout.addWidget(self.chart, 1)

        row = QHBoxLayout()
        row.addStretch()
        btn = QPushButton(_("Close"))
        btn.clicked.connect(self.accept)
        row.addWidget(btn)
        layout.addLayout(row)