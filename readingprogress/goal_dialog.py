"""
Dialog for the yearly reading goal of the "Reading Goal" plugin.

Shows the list books read over the year against a target that grows
evenly to the goal on 31 December, the projection at the pace so far,
all books read according to the library's own data and, optionally,
the previous year. A strip below has the books per month.
"""

from datetime import date, timedelta

from calibre_plugins.readingprogress.chart_common import (
    axis_ticks,
    compute_y_axis,
    is_dark_background,
)
from calibre_plugins.readingprogress.chart_dialog import (
    ALIGN_CENTER,
    ALIGN_RIGHT,
    ALIGN_VCENTER,
    CAP_ROUND,
    JOIN_ROUND,
    LEFT_BUTTON,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    PEN_DASH,
    PEN_DOT,
    PEN_NOPEN,
    PEN_SOLID,
    RENDER_ANTIALIASING,
    RENDER_TEXT_ANTIALIASING,
    TOOLTIP_RADIUS,
    AnnotationRenderer,
    LegendRenderer,
    PlotScale,
    _cursor_pos,
    _global_pos,
    add_export_buttons,
    build_series_colors,
    chrome_for,
    show_paint_error,
)
from calibre_plugins.readingprogress.localization import _
from calibre_plugins.readingprogress.reading_goal import (
    cumulative_dates,
    default_year,
    year_summary,
)
from calibre_plugins.readingprogress.report import (
    goal_header_lines,
    goal_title,
    month_name,
)
from qt.core import (
    QCheckBox,
    QColor,
    QComboBox,
    QDialog,
    QFont,
    QFontMetrics,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPainterPath,
    QPen,
    QPointF,
    QPushButton,
    QRectF,
    Qt,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

CURSOR_HAND  = Qt.CursorShape.PointingHandCursor
CURSOR_ARROW = Qt.CursorShape.ArrowCursor

# Room for the title and three key-figure lines above the plot
MARGIN_TOP = 120

# Monthly strip below the plot: gap above it, its height and the room
# for the month labels below it
STRIP_GAP    = 18
STRIP_HEIGHT = 80
STRIP_BOTTOM = 40

# Headroom above the highest line, so the legend has room
Y_HEADROOM = 1.12

# Bar widths as a share of the month (all read behind, list in front)
BAR_WIDTH_ALL  = 0.7
BAR_WIDTH_LIST = 0.4

# Alpha of the "all read" bars
BAR_ALPHA = 110


def _with_alpha(color, alpha):
    faded = QColor(color)
    faded.setAlpha(alpha)
    return faded


class YearGoalChartWidget(QWidget):
    """Draws one goal year of ``years`` (from
    ``reading_goal.parse_goal_data()``) with the library's ``events``
    (from ``reading_goal.library_events()``)."""

    def __init__(self, years, events, today, date_format, decimal_sep='.',
                 parent=None, colors=None, year=None, compare=False,
                 on_books_clicked=None):
        super().__init__(parent)
        self.years = years
        self.events = events
        self.today = today
        self.date_format = date_format
        self.decimal_sep = decimal_sep
        self.compare = compare
        self.on_books_clicked = on_books_clicked
        self.chrome = chrome_for(self)
        bg = self.chrome['background']
        series = build_series_colors(
            is_dark_background((bg.red(), bg.green(), bg.blue())), colors)
        self.color_list = series['read']
        self.color_target = series['goal']
        self.color_own = series['total']
        self.color_projection = series['forecast']
        self.color_previous = series['soft']
        self._legend = LegendRenderer()
        self._annotation = AnnotationRenderer()
        self.setMinimumSize(700, 500)
        self.setMouseTracking(True)
        self.set_year(year if year in years else default_year(years, today))

    def set_year(self, year):
        self.year = year
        start = date(year, 1, 1)
        self.start = start
        self.end = date(year + 1, 1, 1)
        self.summary = year_summary(self.years[year], self.events,
                                    self.today)
        books = self.years[year]['read']
        self.list_points = cumulative_dates([b['date'] for b in books],
                                            year)
        self.own_points = cumulative_dates(self.events['read'].values(),
                                           year)
        previous = self.years.get(year - 1)
        self.previous_points = []
        if previous is not None:
            # Same day of the year, so both years line up
            prev_start = date(year - 1, 1, 1)
            shifted = [min(start + (b['date'] - prev_start),
                           self.end - timedelta(days=1))
                       for b in previous['read']
                       if b['date'].year == year - 1]
            self.previous_points = cumulative_dates(shifted, year)
        self.update()

    def has_previous(self):
        return bool(self.previous_points)

    def set_compare(self, compare):
        self.compare = compare
        self.update()

    def _line_end(self):
        """Where the lines of read books end: today while the year runs,
        else 1 January of the next year."""
        if self.summary['state'] == 'running':
            return self.today + timedelta(days=1)
        return self.end

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------
    def _plot_rect(self):
        height = (self.height() - MARGIN_TOP - STRIP_GAP - STRIP_HEIGHT
                  - STRIP_BOTTOM)
        return QRectF(MARGIN_LEFT, MARGIN_TOP,
                      max(50, self.width() - MARGIN_LEFT - MARGIN_RIGHT),
                      max(50, height))

    def _strip_rect(self, plot):
        return QRectF(plot.left(), plot.bottom() + STRIP_GAP, plot.width(),
                      STRIP_HEIGHT)

    def _scale(self, plot):
        s = self.summary
        top = [s['goal'], self.own_points[-1][1] if self.own_points else 0,
               s['projection'] or 0]
        if self.compare and self.previous_points:
            top.append(self.previous_points[-1][1])
        y_step, y_max = compute_y_axis(Y_HEADROOM * max(top), integer=True)
        return PlotScale(plot, self.start, (self.end - self.start).days,
                         y_max), y_step

    def _strip_max(self):
        months = self.summary['months'][:self.summary['month_count']]
        return max([max(m['read'], m['list']) for m in months] + [1])

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

        plot = self._plot_rect()
        scale, y_step = self._scale(plot)
        strip = self._strip_rect(plot)

        self._draw_header(painter, plot)
        self._draw_axes(painter, scale, y_step, strip)
        self._draw_strip(painter, scale, strip)

        painter.save()
        painter.setClipRect(plot)
        self._draw_target(painter, scale)
        if self.compare and self.previous_points:
            self._draw_steps(painter, scale, self.previous_points,
                             self.end, self.color_previous, 1.5, PEN_DOT)
        if self.summary['state'] != 'planned':
            self._draw_steps(painter, scale, self.own_points,
                             self._line_end(), self.color_own, 1.5)
            self._draw_projection(painter, scale)
            self._draw_steps(painter, scale, self.list_points,
                             self._line_end(), self.color_list, 2.5)
        painter.restore()

        self._legend.draw_entries(painter, plot, self._legend_entries(),
                                  self.chrome, left=True)
        painter.end()

    def _legend_entries(self):
        entries = [
            (_("Read from the list"), self.color_list, PEN_SOLID),
            (_("Target (evenly over the year)"), self.color_target,
             PEN_DASH),
            (_("Read in total (own data)"), self.color_own, PEN_SOLID),
        ]
        if self.summary['projection'] is not None:
            entries.append((_("Projection at the pace so far"),
                            self.color_projection, PEN_DASH))
        if self.compare and self.previous_points:
            entries.append((_("Previous year {year}").format(
                year=self.year - 1), self.color_previous, PEN_DOT))
        return entries

    def _draw_header(self, painter, plot):
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(self.chrome['text'])
        painter.drawText(QRectF(plot.left(), 15, plot.width(), 30),
                         ALIGN_CENTER,
                         goal_title(self.summary, _, self.decimal_sep))
        self._annotation.draw_pace(
            painter, plot, self.width(),
            goal_header_lines(self.summary, _, self.date_format,
                              self.decimal_sep), self.chrome)

    def _draw_axes(self, painter, scale, y_step, strip):
        plot = scale.plot
        chrome = self.chrome
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        for y_value in axis_ticks(scale.y_max, y_step):
            y_pix = scale.value_to_y(y_value)
            pen = QPen(chrome['grid'], 1)
            pen.setStyle(PEN_DOT)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(), y_pix),
                             QPointF(plot.right(), y_pix))
            painter.setPen(chrome['text'])
            text = str(int(y_value))
            width = fm.horizontalAdvance(text)
            painter.drawText(
                QRectF(plot.left() - 10 - width, y_pix - 8, width, 16),
                ALIGN_RIGHT | ALIGN_VCENTER, text)

        # Month boundaries through plot and strip, labels below the strip
        for month in range(1, 13):
            x = scale.date_to_x(date(self.year, month, 1))
            x_next = scale.date_to_x(date(self.year + 1, 1, 1)
                                     if month == 12
                                     else date(self.year, month + 1, 1))
            if month > 1:
                pen = QPen(chrome['grid'], 1)
                pen.setStyle(PEN_DOT)
                painter.setPen(pen)
                painter.drawLine(QPointF(x, plot.top()),
                                 QPointF(x, strip.bottom()))
            painter.setPen(chrome['text'])
            painter.drawText(QRectF(x, strip.bottom() + 6, x_next - x, 18),
                             ALIGN_CENTER, month_name(_, month))

        painter.setPen(QPen(chrome['axis'], 1))
        for rect in (plot, strip):
            painter.drawLine(QPointF(rect.left(), rect.top()),
                             QPointF(rect.left(), rect.bottom()))
            painter.drawLine(QPointF(rect.left(), rect.bottom()),
                             QPointF(rect.right(), rect.bottom()))

        title_font = QFont()
        title_font.setPointSize(11)
        painter.setFont(title_font)
        painter.setPen(chrome['text'])
        painter.save()
        painter.translate(20, plot.center().y())
        painter.rotate(-90)
        painter.drawText(QRectF(-plot.height() / 2, -10, plot.height(), 20),
                         ALIGN_CENTER, _("Number of books"))
        painter.restore()
        painter.save()
        painter.translate(20, strip.center().y())
        painter.rotate(-90)
        painter.setFont(font)
        painter.drawText(QRectF(-strip.height() / 2 - 20, -10,
                                strip.height() + 40, 20),
                         ALIGN_CENTER, _("Per month"))
        painter.restore()

    def _month_span(self, scale, month):
        x0 = scale.date_to_x(date(self.year, month, 1))
        x1 = scale.date_to_x(date(self.year + 1, 1, 1) if month == 12
                             else date(self.year, month + 1, 1))
        return x0, x1

    def _draw_strip(self, painter, scale, strip):
        months = self.summary['months'][:self.summary['month_count']]
        if not months:
            return
        top = self._strip_max()
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(self.chrome['muted'])
        painter.drawText(QRectF(strip.left() - 40, strip.top() - 8, 30, 16),
                         ALIGN_RIGHT | ALIGN_VCENTER, str(top))
        painter.setPen(QPen(PEN_NOPEN))
        for i, m in enumerate(months):
            x0, x1 = self._month_span(scale, i + 1)
            for value, share, color in (
                    (m['read'], BAR_WIDTH_ALL,
                     _with_alpha(self.color_own, BAR_ALPHA)),
                    (m['list'], BAR_WIDTH_LIST, self.color_list)):
                if not value:
                    continue
                width = (x1 - x0) * share
                height = strip.height() * value / top
                painter.setBrush(color)
                painter.drawRect(QRectF((x0 + x1 - width) / 2,
                                        strip.bottom() - height,
                                        width, height))

    def _draw_target(self, painter, scale):
        goal = self.summary['goal']
        pen = QPen(self.color_target, 2)
        pen.setStyle(PEN_DASH)
        pen.setCapStyle(CAP_ROUND)
        painter.setPen(pen)
        y_goal = scale.value_to_y(goal)
        painter.drawLine(QPointF(scale.date_to_x(self.start),
                                 scale.value_to_y(0)),
                         QPointF(scale.date_to_x(self.end), y_goal))
        pen = QPen(self.color_target, 1)
        pen.setStyle(PEN_DOT)
        painter.setPen(pen)
        painter.drawLine(QPointF(scale.plot.left(), y_goal),
                         QPointF(scale.plot.right(), y_goal))

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(self.color_target)
        text = _("Goal: {books}").format(books=goal)
        width = QFontMetrics(font).horizontalAdvance(text)
        painter.drawText(QRectF(scale.plot.right() - width - 8, y_goal - 20,
                                width, 16), ALIGN_RIGHT | ALIGN_VCENTER,
                         text)

    def _draw_steps(self, painter, scale, points, end, color, width,
                    style=PEN_SOLID):
        """Running total as a step line from 1 January to ``end``."""
        pen = QPen(color, width)
        pen.setStyle(style)
        pen.setCapStyle(CAP_ROUND)
        pen.setJoinStyle(JOIN_ROUND)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath(QPointF(scale.date_to_x(self.start),
                                    scale.value_to_y(0)))
        for day, count in points:
            if day >= end:
                break
            x = scale.date_to_x(day)
            path.lineTo(QPointF(x, path.currentPosition().y()))
            path.lineTo(QPointF(x, scale.value_to_y(count)))
        path.lineTo(QPointF(scale.date_to_x(end),
                            path.currentPosition().y()))
        painter.drawPath(path)

    def _draw_projection(self, painter, scale):
        s = self.summary
        if s['projection'] is None:
            return
        pen = QPen(self.color_projection, 2)
        pen.setStyle(PEN_DASH)
        pen.setCapStyle(CAP_ROUND)
        painter.setPen(pen)
        start = QPointF(scale.date_to_x(self._line_end()),
                        scale.value_to_y(s['read']))
        end = QPointF(scale.date_to_x(self.end),
                      scale.value_to_y(s['projection']))
        painter.drawLine(start, end)
        painter.setPen(QPen(self.color_list, 1))
        painter.setBrush(self.color_list)
        painter.drawEllipse(start, 4, 4)

    # ------------------------------------------------------------------
    # Tooltips and clicks
    # ------------------------------------------------------------------
    def _books_at(self, pos):
        """Read list books of the step nearest to ``pos``, or []."""
        if self.summary['state'] == 'planned':
            return []
        plot = self._plot_rect()
        if not plot.contains(pos):
            return []
        scale = self._scale(plot)[0]
        best, best_dist = None, TOOLTIP_RADIUS
        for day, count in self.list_points:
            dist = abs(scale.date_to_x(day) - pos.x())
            if dist < best_dist:
                best, best_dist = day, dist
        if best is None:
            return []
        return [b for b in self.years[self.year]['read']
                if b['date'] == best]

    def _month_at(self, pos):
        plot = self._plot_rect()
        strip = self._strip_rect(plot)
        if not strip.contains(pos):
            return None
        scale = self._scale(plot)[0]
        for month in range(1, self.summary['month_count'] + 1):
            x0, x1 = self._month_span(scale, month)
            if x0 <= pos.x() < x1:
                return month
        return None

    def mouseMoveEvent(self, event):
        pos = _cursor_pos(event)
        books = self._books_at(pos)
        if books:
            self.setCursor(CURSOR_HAND if self.on_books_clicked
                           else CURSOR_ARROW)
            count = next(c for d, c in self.list_points
                         if d == books[0]['date'])
            lines = [_("{date}: {count} of {goal} books").format(
                date=books[0]['date'].strftime(self.date_format),
                count=count, goal=self.summary['goal'])]
            for b in books:
                lines.append(_("{title} – {authors}").format(
                    title=b['title'], authors=b['authors'])
                    if b['authors'] else b['title'])
            QToolTip.showText(_global_pos(event), '\n'.join(lines), self)
            return
        self.setCursor(CURSOR_ARROW)
        month = self._month_at(pos)
        if month is None:
            QToolTip.hideText()
            return
        m = self.summary['months'][month - 1]
        QToolTip.showText(_global_pos(event), _(
            "{month} {year}\nFrom the list: {list}\n"
            "Read in total: {read}\nAdded: {added}").format(
            month=month_name(_, month), year=self.year, list=m['list'],
            read=m['read'], added=m['added']), self)

    def mousePressEvent(self, event):
        if event.button() != LEFT_BUTTON or self.on_books_clicked is None:
            return
        books = self._books_at(_cursor_pos(event))
        if books:
            self.on_books_clicked([b['book_id'] for b in books])


class YearGoalDialog(QDialog):
    """Dialog with the yearly-goal chart, year selector, previous-year
    comparison, export buttons and Close.

    ``on_show(book_ids)`` displays books in calibre's book list; the
    dialog closes before it is called.
    """

    def __init__(self, years, events, today, date_format, decimal_sep='.',
                 parent=None, colors=None, on_show=None):
        super().__init__(parent)
        self.on_show = on_show
        self.setWindowTitle(_("Reading goal (Reading Goal plugin)"))
        self.resize(1200, 800)

        layout = QVBoxLayout(self)
        self.chart = YearGoalChartWidget(
            years, events, today, date_format, decimal_sep, self,
            colors=colors, on_books_clicked=self._show)
        layout.addWidget(self.chart, 1)

        row = QHBoxLayout()
        self.year_box = QComboBox(self)
        for year in sorted(years, reverse=True):
            self.year_box.addItem(str(year), year)
        self.year_box.setCurrentIndex(self.year_box.findData(
            self.chart.year))
        self.year_box.currentIndexChanged.connect(self._year_changed)
        row.addWidget(QLabel(_("Year:"), self))
        row.addWidget(self.year_box)

        self.compare_box = QCheckBox(_("Compare with the previous year"),
                                     self)
        self.compare_box.toggled.connect(self.chart.set_compare)
        row.addWidget(self.compare_box)
        self._update_compare()

        row.addWidget(QLabel(_("Click a step to show its books in "
                               "calibre."), self))
        row.addStretch()
        add_export_buttons(row, self.chart, 'reading-goal')
        btn = QPushButton(_("Close"))
        btn.clicked.connect(self.reject)
        row.addWidget(btn)
        layout.addLayout(row)

    def _year_changed(self, index):
        self.chart.set_year(self.year_box.itemData(index))
        self._update_compare()

    def _update_compare(self):
        self.compare_box.setEnabled(self.chart.has_previous())

    def _show(self, book_ids):
        self.accept()
        if self.on_show is not None:
            self.on_show(book_ids)
