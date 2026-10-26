"""
Dialog for the age distribution of the backlog (TBR).

One bar per whole year of age of the unread books. Clicking a bar shows
those books in calibre's book list.
"""

from calibre_plugins.readingprogress.chart_common import (
    compute_y_axis,
    is_dark_background,
)
from calibre_plugins.readingprogress.chart_dialog import (
    ALIGN_CENTER,
    ALIGN_RIGHT,
    ALIGN_VCENTER,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    PEN_DOT,
    PEN_NOPEN,
    RENDER_ANTIALIASING,
    RENDER_TEXT_ANTIALIASING,
    _cursor_pos,
    _global_pos,
    _qt_enum,
    add_export_buttons,
    build_series_colors,
    chrome_for,
    show_paint_error,
)
from calibre_plugins.readingprogress.localization import _
from qt.core import (
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

# Room for title and key-figures line above, labels below the plot
MARGIN_TOP    = 95
MARGIN_BOTTOM = 70

# Bar width as a share of its slot
BAR_SHARE = 0.7

# Headroom above the highest bar for its count label
Y_HEADROOM = 1.1

CURSOR_HAND  = _qt_enum(['CursorShape', 'PointingHandCursor'],
                        ['PointingHandCursor'])
CURSOR_ARROW = _qt_enum(['CursorShape', 'ArrowCursor'], ['ArrowCursor'])


def bucket_label(index, bucket_count, max_years):
    """'< 1 year', '2–3 years' or, for a capped last bucket, '10+ years'."""
    if index == 0:
        return _("< 1 year")
    if index == max_years and index == bucket_count - 1:
        return _("{years}+ years").format(years=index)
    return _("{start}–{end} years").format(start=index, end=index + 1)


class AgeChartWidget(QWidget):
    """Draws the age distribution as bars.

    ``buckets`` is the list from ``age_buckets()`` (book ids per year of
    age); ``on_bar_clicked(book_ids)`` is called for a click on a bar.
    """

    def __init__(self, buckets, max_years, summary, decimal_sep='.',
                 parent=None, colors=None, on_bar_clicked=None):
        super().__init__(parent)
        self.buckets = buckets
        self.max_years = max_years
        self.summary = summary
        self.decimal_sep = decimal_sep
        self.on_bar_clicked = on_bar_clicked
        self.total = sum(len(b) for b in buckets)
        self.chrome = chrome_for(self)
        bg = self.chrome['background']
        series = build_series_colors(
            is_dark_background((bg.red(), bg.green(), bg.blue())), colors)
        self.color_bar = series['backlog']
        self.color_hover = series['backlog'].lighter(125)
        self._hover = None
        self.setMinimumSize(700, 450)
        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------
    def _plot_rect(self):
        return QRectF(
            MARGIN_LEFT,
            MARGIN_TOP,
            max(50, self.width()  - MARGIN_LEFT - MARGIN_RIGHT),
            max(50, self.height() - MARGIN_TOP  - MARGIN_BOTTOM),
        )

    def _y_axis(self):
        largest = max(len(b) for b in self.buckets)
        return compute_y_axis(Y_HEADROOM * largest)

    def _bar_rect(self, plot, index, y_max):
        slot = plot.width() / len(self.buckets)
        width = slot * BAR_SHARE
        height = plot.height() * len(self.buckets[index]) / y_max
        return QRectF(plot.left() + index * slot + (slot - width) / 2,
                      plot.bottom() - height, width, height)

    def _bar_at(self, pos):
        """Index of the bar slot under ``pos`` (a non-empty one), or None."""
        plot = self._plot_rect()
        if not plot.contains(pos) or not self.total:
            return None
        index = int((pos.x() - plot.left()) / (plot.width()
                                                / len(self.buckets)))
        if 0 <= index < len(self.buckets) and self.buckets[index]:
            return index
        return None

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

        if not self.total:
            painter.setPen(self.chrome['text'])
            painter.drawText(self.rect(), ALIGN_CENTER, _("No data"))
            painter.end()
            return

        plot = self._plot_rect()
        y_step, y_max = self._y_axis()
        self._draw_header(painter, plot)
        self._draw_axes(painter, plot, y_step, y_max)
        self._draw_bars(painter, plot, y_max)
        painter.end()

    def _draw_header(self, painter, plot):
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(self.chrome['text'])
        painter.drawText(QRectF(plot.left(), 15, plot.width(), 30),
                         ALIGN_CENTER, _("Age of the TBR"))

        s = self.summary
        median = '{:.1f}'.format(s['median_years']).replace(
            '.', self.decimal_sep)
        text = _("{count} unread books · median age {median} years · "
                 "oldest added in {year}").format(
            count=self.total, median=median, year=s['oldest_year'])
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)
        painter.setPen(self.chrome['muted'])
        painter.drawText(QRectF(plot.left(), 50, plot.width(), 22),
                         ALIGN_CENTER, text)

    def _draw_axes(self, painter, plot, y_step, y_max):
        painter.setPen(QPen(self.chrome['axis'], 1))
        painter.drawLine(QPointF(plot.left(), plot.top()),
                         QPointF(plot.left(), plot.bottom()))
        painter.drawLine(QPointF(plot.left(), plot.bottom()),
                         QPointF(plot.right(), plot.bottom()))

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        value = y_step
        while value <= y_max + 0.01:
            y = plot.bottom() - plot.height() * value / y_max
            pen = QPen(self.chrome['grid'], 1)
            pen.setStyle(PEN_DOT)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(), y),
                             QPointF(plot.right(), y))
            painter.setPen(self.chrome['text'])
            text = str(int(value))
            width = fm.horizontalAdvance(text)
            painter.drawText(QRectF(plot.left() - 10 - width, y - 8,
                                    width, 16),
                             ALIGN_RIGHT | ALIGN_VCENTER, text)
            value += y_step

        slot = plot.width() / len(self.buckets)
        for index in range(len(self.buckets)):
            label = bucket_label(index, len(self.buckets), self.max_years)
            painter.drawText(QRectF(plot.left() + index * slot,
                                    plot.bottom() + 6, slot, 18),
                             ALIGN_CENTER, label)

        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)
        painter.drawText(QRectF(plot.left(), plot.bottom() + 34,
                                plot.width(), 20),
                         ALIGN_CENTER, _("Time in the TBR"))
        painter.save()
        painter.translate(20, plot.center().y())
        painter.rotate(-90)
        painter.drawText(QRectF(-plot.height() / 2, -10, plot.height(), 20),
                         ALIGN_CENTER, _("Number of books"))
        painter.restore()

    def _draw_bars(self, painter, plot, y_max):
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        for index, ids in enumerate(self.buckets):
            if not ids:
                continue
            rect = self._bar_rect(plot, index, y_max)
            painter.setPen(QPen(PEN_NOPEN))
            painter.setBrush(self.color_hover if index == self._hover
                             else self.color_bar)
            painter.drawRect(rect)
            painter.setPen(self.chrome['text'])
            painter.drawText(QRectF(rect.left() - 10, rect.top() - 20,
                                    rect.width() + 20, 18),
                             ALIGN_CENTER, str(len(ids)))

    # ------------------------------------------------------------------
    # Interaction: hover tooltip, click shows the books
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        index = self._bar_at(_cursor_pos(event))
        if index != self._hover:
            self._hover = index
            self.setCursor(CURSOR_HAND if index is not None
                           else CURSOR_ARROW)
            self.update()
        if index is None:
            QToolTip.hideText()
            return
        count = len(self.buckets[index])
        share = '{:.0f}'.format(100 * count / self.total)
        text = _("{label}\n{count} books · {share} %\n"
                 "Click to show them in calibre").format(
            label=bucket_label(index, len(self.buckets), self.max_years),
            count=count, share=share)
        QToolTip.showText(_global_pos(event), text, self)

    def leaveEvent(self, event):
        if self._hover is not None:
            self._hover = None
            self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        index = self._bar_at(_cursor_pos(event))
        if index is not None and self.on_bar_clicked is not None:
            self.on_bar_clicked(self.buckets[index])


class AgeChartDialog(QDialog):
    """Dialog with the age chart, export buttons and Close.

    ``on_show(book_ids)`` displays books in calibre's book list; the
    dialog closes before it is called.
    """

    def __init__(self, buckets, max_years, summary, decimal_sep='.',
                 parent=None, colors=None, on_show=None):
        super().__init__(parent)
        self.on_show = on_show
        self.setWindowTitle(_("Age of the TBR"))
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        self.chart = AgeChartWidget(buckets, max_years, summary, decimal_sep,
                                    self, colors=colors,
                                    on_bar_clicked=self._show)
        layout.addWidget(self.chart, 1)

        row = QHBoxLayout()
        row.addWidget(QLabel(_("Click a bar to show its books in calibre."),
                             self))
        row.addStretch()
        add_export_buttons(row, self.chart, 'tbr-age')
        btn = QPushButton(_("Close"))
        btn.clicked.connect(self.reject)
        row.addWidget(btn)
        layout.addLayout(row)

    def _show(self, book_ids):
        self.accept()
        if self.on_show is not None:
            self.on_show(book_ids)
